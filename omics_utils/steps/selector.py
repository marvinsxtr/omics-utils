from pathlib import Path

import dask.dataframe as dd
import pandas as pd
import scanpy as sc
from dask.distributed import print
from hydra_zen.typing import Partial

from omics_utils.pipeline.step import Step
from omics_utils.transforms.anndata_filterer import AnnDataFilterer
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import read_anndata_dask


class Selector(Step):
    """Selects the genes used in consecutive preprocessing steps."""

    def __init__(
        self,
        *args,
        input_dir: str,
        filterer: Partial[AnnDataFilterer],
        n_debug: int | None = None,
        subset: list[str] | None = None,
        n_highly_variable: int = 5000,
        **kwargs,
    ) -> None:
        """
        Args:
            input_dir: Folder where the input CellXGene `AnnData` files are saved.
            filterer: Filter to apply to each individual `AnnData` file.
            n_debug: Take the first n input files only for debugging purposes.
            subset: Subset of .h5ad file names to process.
            n_highly_variable: Number of highly variable genes to take per sub-dataset.
        """  # noqa: D212
        super().__init__(*args, **kwargs)
        raw_input_path = Path(input_dir)

        if not raw_input_path.exists():
            raise ValueError("Input path does not exist.")

        self.filterer = filterer()
        self.raw_input_path = raw_input_path
        self.n_debug = n_debug
        self.subset = subset
        self.n_highly_variable = n_highly_variable

    @property
    def input_step(self) -> str | None:
        """Has no preceding preprocessing step."""
        return None

    @property
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        return "cols"

    @property
    def meta_df(self) -> pd.DataFrame:
        """Empty `DataFrame` used by Dask to determine the output of `transform`."""
        return pd.DataFrame(
            columns=[ColumnNames.BATCH_ID, ColumnNames.COLUMN_ID, ColumnNames.HIGHLY_VARIABLE],
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

        if self.subset is not None:
            input_files = [f for f in input_files if f.stem in self.subset]

        return dd.from_map(self.transform, input_files, meta=self.meta_df)

    def transform(self, file_path: Path) -> pd.DataFrame:
        """Preprocess a single `AnnData` file.

        Args:
            file_path: Path to the `AnnData` file to be transformed.

        Returns:
            A list of `Delayed` tasks for preprocessing.
        """
        batch_id = str(file_path.stem)
        adata = read_anndata_dask(file_path)
        adata = self.filterer(adata, batch_id=batch_id)

        if adata.n_obs == 0:
            return self.meta_df

        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)
        sc.pp.highly_variable_genes(adata, n_top_genes=self.n_highly_variable, flavor="cell_ranger")

        df = adata.var[ColumnNames.HIGHLY_VARIABLE].to_frame(name=ColumnNames.HIGHLY_VARIABLE)
        df[ColumnNames.BATCH_ID] = batch_id
        return df.reset_index(names=ColumnNames.COLUMN_ID)

    def write(self, data_df: dd.DataFrame) -> None:
        """Load/save the result of the transformation.

        Args:
            data_df: A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        pass

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read` and `write`."""
        input_files = list(self.raw_input_path.glob("*.h5ad"))
        df = self.read(input_files).compute()
        print(df)
