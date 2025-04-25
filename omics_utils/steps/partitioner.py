import itertools
import uuid
from abc import ABC
from pathlib import Path

import dask.bag as db
import dask.dataframe as dd
import pandas as pd
from dask.delayed import Delayed
from hydra_zen.typing import Partial

from omics_utils.pipeline.step import Step
from omics_utils.transforms.anndata_converter import AnnDataConverter
from omics_utils.transforms.anndata_filterer import AnnDataFilterer
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import read_anndata_dask, read_var_cols


class Partitioner(Step, ABC):
    """Partitioner for `AnnData` files."""

    def __init__(
        self,
        *args,
        input_dir: str,
        converter: Partial[AnnDataConverter],
        filterer: Partial[AnnDataFilterer],
        n_outer_partitions: int = 50,
        n_inner_partitions: int = 10,
        n_debug: int | None = None,
        subset: list[str] | None = None,
        **kwargs,
    ) -> None:
        """
        Args:
            input_dir: Folder where the input CellXGene `AnnData` files are saved.
            converter: Converter to convert `AnnData` into a `DataFrame` format.
            filterer: Filter to apply to each individual `AnnData` file.
            n_debug: Take the first n input files only for debugging purposes.
            n_outer_partitions: Number of output partitions.
            n_inner_partitions: Number of output partitions within each outer partition.
            subset: Subset of .h5ad file names to process.
            only_primary: Whether to only process cells marked as primary data.
        """  # noqa: D212
        super().__init__(*args, **kwargs)
        raw_input_path = Path(input_dir)

        if not raw_input_path.exists():
            raise ValueError("Input path does not exist.")

        self.converter = converter
        self.filterer = filterer
        self.raw_input_path = raw_input_path
        self.n_outer_partitions = n_outer_partitions
        self.n_inner_partitions = n_inner_partitions
        self.n_debug = n_debug
        self.subset = subset

    @property
    def input_step(self) -> str | None:
        """Has no preceding preprocessing step."""
        return "genes"

    @property
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        return "data"

    @property
    def meta_df(self) -> pd.DataFrame:
        """Empty `DataFrame` used by Dask to determine the output of `transform`."""
        return pd.DataFrame(
            columns=[
                ColumnNames.SPARSE_VECTOR,
                ColumnNames.CASE_ID,
                ColumnNames.SAMPLE_ID,
                ColumnNames.BATCH_ID,
                *self.converter.obs_cols,
            ],
            index=pd.Index([], dtype=str),
            dtype=str,
        )

    def read(self, input_files: list[Path]) -> dd.DataFrame:
        """Read and transform the data from the the input data.

        NOTE: In this case the read step contains the transform step for compatibility with dask.

        Args:
            input_files: File paths to process in parallel.

        Returns:
            The data ready for transformation.
        """
        var_cols = read_var_cols(self.input_path / "genes.csv")

        self.converter = self.converter(var_cols=var_cols)
        self.filterer = self.filterer(var_cols=var_cols)

        if self.n_debug is not None:
            input_files = input_files[: self.n_debug]

        if self.subset is not None:
            input_files = [f for f in input_files if f.stem in self.subset]

        return (
            db.from_sequence(input_files)
            .map(self.transform)
            .flatten()
            .repartition(npartitions=self.n_outer_partitions)
        )

    def transform(self, file_path: Path) -> list[Delayed]:
        """Preprocess a single `AnnData` file.

        Args:
            file_path: Path to the `AnnData` file to be transformed.

        Returns:
            A list of `Delayed` tasks for preprocessing.
        """
        adata = read_anndata_dask(file_path)
        adata = self.filterer(adata, batch_id=str(file_path.stem))
        return self.converter.anndata_to_dataframe(adata)

    def write(self, data_df: dd.DataFrame) -> None:
        """Load/save the result of the transformation.

        Args:
            data_df: A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        data_df.repartition(npartitions=self.n_inner_partitions, force=True).to_parquet(
            self.output_path, filesystem="arrow", name_function=lambda _: f"{uuid.uuid4()!s}.parquet"
        )

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read` and `write`."""
        input_files = list(self.raw_input_path.glob("*.h5ad"))
        delayed = self.read(input_files)

        def process(delayed_iterator: itertools.chain) -> None:
            """Process a partition of tasks."""
            delayed_list = list(delayed_iterator)

            if len(delayed_list) > 0:
                data_df = dd.from_delayed(delayed_list, meta=self.meta_df)
                self.write(data_df)

        delayed.map_partitions(process).compute()
