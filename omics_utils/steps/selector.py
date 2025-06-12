from pathlib import Path

import dask.dataframe as dd
import pandas as pd
import scanpy as sc
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
        var_cols: dict[str, str],
        n_debug: int | None = None,
        subset: list[str] | None = None,
        n_highly_variable: int | None = None,
        gene_file: str | None = None,
        **kwargs,
    ) -> None:
        """
        Args:
            input_dir: Folder where the input CellXGene `AnnData` files are saved.
            filterer: Filter to apply to each individual `AnnData` file.
            var_cols: Subset of columns in the `var` `DataFrame` to keep and their respective dtype.
            n_debug: Take the first n input files only for debugging purposes.
            subset: Subset of .h5ad file names to process.
            n_highly_variable: Number of highly variable genes to take per sub-dataset.
            gene_file: File to load the selected genes from. Ignores all other kwargs.
        """  # noqa: D212
        super().__init__(*args, **kwargs)

        if (n_highly_variable is not None and gene_file is not None) or (
            n_highly_variable is None and gene_file is None
        ):
            raise ValueError("Either select the HVGs or provide a list of genes to use.")

        raw_input_path = Path(input_dir) if input_dir is not None else None

        if raw_input_path is not None and not raw_input_path.exists():
            raise ValueError("Input path does not exist.")

        self.genes = pd.read_parquet(gene_file).index.to_list() if gene_file is not None else None
        self.filterer = filterer(genes=self.genes)
        self.raw_input_path = raw_input_path
        self.n_debug = n_debug
        self.subset = subset
        self.n_highly_variable = n_highly_variable
        self.var_cols = var_cols

    @property
    def input_step(self) -> str | None:
        """Has no preceding preprocessing step."""
        return None

    @property
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        return "genes"

    @property
    def meta_df(self) -> pd.DataFrame:
        """Empty `DataFrame` used by Dask to determine the output of `transform`."""
        cols = {ColumnNames.GENE_ID: "str"}

        if self.n_highly_variable is not None:
            cols.update({ColumnNames.HIGHLY_VARIABLE: "bool", ColumnNames.DISPERSIONS_NORM: "float"})

        cols.update(self.var_cols)

        return pd.DataFrame(
            {k: pd.Series(dtype=v) for k, v in cols.items()},
            index=pd.Index([], dtype=str),
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

        if adata is None:
            return self.meta_df

        adata = self.filterer(adata, batch_id=batch_id)

        if adata.n_obs == 0:
            return self.meta_df

        var_cols = list(self.var_cols.keys())

        if self.n_highly_variable is not None:
            sc.pp.normalize_total(adata, target_sum=1e4)
            sc.pp.log1p(adata)
            sc.pp.highly_variable_genes(adata, n_top_genes=self.n_highly_variable)

            var_cols += [ColumnNames.HIGHLY_VARIABLE, ColumnNames.DISPERSIONS_NORM]

        return adata.var[var_cols].reset_index(names=ColumnNames.GENE_ID)

    def write(self, data_df: dd.DataFrame) -> None:
        """Rank the genes by number of batches they are HVG and break ties by dispersion norm.

        Args:
            data_df: `DataFrame` containing a gene id, a highly variable gene flag and the dispersion norm.
        """
        if self.n_highly_variable is None:
            var_ddf = data_df.drop_duplicates(subset=[ColumnNames.GENE_ID])
            var_df: pd.DataFrame = var_ddf.compute()
            var_df.set_index(ColumnNames.GENE_ID, drop=True).to_parquet(self.output_path / "genes.parquet")
            return

        data_df = data_df[data_df[ColumnNames.HIGHLY_VARIABLE] == True]
        data_df[ColumnNames.HIGHLY_VARIABLE] = data_df[ColumnNames.HIGHLY_VARIABLE].astype(int)

        agg_dict = {
            ColumnNames.HIGHLY_VARIABLE: "sum",
            ColumnNames.DISPERSIONS_NORM: "mean",
        }

        aggregated_ddf = data_df.groupby(ColumnNames.GENE_ID).agg(agg_dict).reset_index()
        ranking_ddf = aggregated_ddf.sort_values(
            [ColumnNames.HIGHLY_VARIABLE, ColumnNames.DISPERSIONS_NORM], ascending=False
        )
        ranking_ddf = ranking_ddf.reset_index(drop=True)

        ranking_df: pd.DataFrame = ranking_ddf.compute()
        ranking_df = ranking_df.set_index(ColumnNames.GENE_ID, drop=True)

        ranking_df.to_parquet(self.output_path / "ranking.parquet")
        ranking_df.head(self.n_highly_variable).to_parquet(self.output_path / "genes.parquet")

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read` and `write`."""
        input_files = list(self.raw_input_path.glob("*.h5ad"))
        data_df = self.read(input_files)
        self.write(data_df)
