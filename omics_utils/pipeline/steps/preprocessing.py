from abc import ABC, abstractmethod
from pathlib import Path

import dask.dataframe as dd
import pandas as pd

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.pipeline.step import Step
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import remove_empty_partitions


class Preprocessing(Step, ABC):
    """Base class for preprocessing of `AnnData` files."""

    def __init__(
        self,
        *args,
        converter: AnndataConverter,
        input_dir: str,
        n_partitions: int = 100,
        n_debug: int | None = None,
        meta_partition_size: int | None = None,
        **kwargs,
    ) -> None:
        """
        Args:
            converter: Converter used to transform AnnData objects into DataFrames and the other way around.
            input_dir: Folder where the input `AnnData` files are saved.
            n_partitions: Number of output partitions.
            n_debug: Take the first n input files only for debugging purposes.
            meta_partition_size: Number of files to process at a time, useful for saving resources.
        """  # noqa: D212
        super().__init__(*args, **kwargs)
        input_path = Path(input_dir)

        if not input_path.exists():
            raise ValueError("Input path does not exist.")

        self.converter = converter
        self.input_path = input_path
        self.n_partitions = n_partitions
        self.n_debug = n_debug
        self.meta_partition_size = meta_partition_size

    @property
    def input_step(self) -> str | None:
        """Has no preceding preprocessing step."""
        return None

    @property
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        return "data"

    @property
    def meta_df(self) -> pd.DataFrame:
        """Empty `DataFrame` used by Dask to determine the output of `transform`."""
        return pd.DataFrame(
            columns=[ColumnNames.SPARSE_VECTOR, ColumnNames.CASE_ID,
                     ColumnNames.SAMPLE_ID, *self.converter.obs_cols],
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
        if self.n_debug is not None:
            input_files = input_files[: self.n_debug]

        data_df = dd.from_map(self.transform, input_files)
        data_df = remove_empty_partitions(data_df)
        return data_df

    @abstractmethod
    def transform(self, file_path: Path) -> pd.DataFrame:
        """Transform a single `AnnData` file."""
        ...

    def write(self, data_df: dd.DataFrame, meta_partition_index: int = 0) -> None:
        """Load/save the result of the transformation.

        Args:
            data_df: A `DataFrame` containing the patient/donor metadata and the matrix `X`.
            meta_partition_index: Index of the sequential processing partition.
        """
        data_df.repartition(npartitions=self.n_partitions, force=True).to_parquet(
            self.output_path,
            filesystem="arrow",
            name_function=lambda chunk: f"part_{meta_partition_index}_chunk_{chunk}.parquet",
        )

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read` and `write`."""
        input_files = list(self.input_path.glob("*.h5ad"))

        if self.meta_partition_size is not None:
            for i, j in enumerate(range(0, len(input_files), self.meta_partition_size)):
                data_df = self.read(
                    input_files[j: j + self.meta_partition_size])
                self.write(data_df, meta_partition_index=i)
        else:
            data_df = self.read(input_files)
            self.write(data_df)
