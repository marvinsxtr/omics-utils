from pathlib import Path

import anndata as ad
import dask.dataframe as dd
import pandas as pd
import scipy.sparse as sp
import yaml

from omics_utils.preprocessing.steps.step import PreprocessingStep
from omics_utils.splitting.splitter import Splitter
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import global_reset_index


class Stratifier(PreprocessingStep):
    """Preprocessing step which reads case metadata, performs stratification and splits the data accordingly."""

    def __init__(
        self, *args, splitter: Splitter, metadata_columns: list[str], partition_size: str = "10GB", **kwargs
    ) -> None:
        """Args:
        ----
          splitter: Splitter to use for stratification, grouping and shuffling among folds.
          metadata_columns: List of columns that should be extracted as metadata from the `DataFrame`.
          partition_size: The size of the resulting partitions in MB/GB. Should not be larger than memory.
        """
        super().__init__(*args, **kwargs)

        metadata_path = self.output_path / "metadata.parquet"
        split_path = self.output_path / "split"

        self.splitter = splitter
        self.metadata_columns = metadata_columns
        self.partition_size = partition_size
        self.metadata_path = metadata_path
        self.split_path = split_path

    @property
    def input_step(self) -> str:
        """Name of the prceding preprocessing step."""
        return "data"

    @property
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        return "stratification"

    def read(self) -> dd.DataFrame:
        """Read the data from the previous step.

        Returns
        -------
        The data ready for transformation.
        """
        return dd.from_map(pd.read_parquet, self.input_path.glob("*.parquet"))

    def transform(self, data_df: dd.DataFrame) -> tuple[dict[int, dd.DataFrame], pd.DataFrame]:
        """Extract the metadata and perform splitting.

        Args:
        ----
          data_df: The input `DataFrame`.

        Returns:
        -------
        A tuple of a dict containing a mapping of the fold index to the data split and the metadata `DataFrame`.
        """
        metadata_df: pd.DataFrame = (
            data_df[[ColumnNames.CASE_ID, *self.metadata_columns]].drop_duplicates().reset_index(drop=True).compute()
        )
        metadata_df = metadata_df.set_index(ColumnNames.CASE_ID)
        metadata_df = self.splitter.split(metadata_df)

        joined_df: dd.DataFrame = data_df.join(metadata_df[[ColumnNames.FOLD]], on=ColumnNames.CASE_ID)

        folds = {}
        for fold_idx in range(self.splitter.num_folds):
            fold_df: dd.DataFrame = joined_df[joined_df[ColumnNames.FOLD] == fold_idx].sample(
                frac=1, random_state=self.splitter.seed
            )
            fold_df = global_reset_index(fold_df).compute_current_divisions(set_divisions=True)
            folds[fold_idx] = fold_df

        return folds, metadata_df

    def df_to_anndata(
        self, df: pd.DataFrame, output_dir: Path, fold_idx: int, partition_info: dict | None = None
    ) -> None:
        """Write a `DataFrame` to an anndata file."""
        part = partition_info["number"]
        gene_cols = list(set(df.columns) - set(self.metadata_columns) - set(ColumnNames.FOLD))
        x_matrix = sp.csr_matrix(df[gene_cols].to_numpy())
        adata = ad.AnnData(X=x_matrix, obs=df[self.metadata_columns])
        adata.write_h5ad(output_dir / f"fold_{fold_idx}_part_{part}.h5ad")

    def write(self, folds: dict[int, dd.DataFrame], metadata_df: pd.DataFrame) -> None:
        """Save the folds and the case metadata separately.

        Args:
        ----
          folds: A dict containing a mapping of the fold index to the data split.
          metadata_df: The metadata `DataFrame`.
        """
        metadata_df.to_parquet(self.metadata_path)

        self.split_path.mkdir(exist_ok=True)

        limits = {}
        for fold_idx, fold_df in folds.items():
            limits[fold_idx] = list(fold_df.divisions)[1:]

            fold_df.map_partitions(self.df_to_anndata, self.split_path, fold_idx, meta=fold_df.head()).compute()
            # fold_df.to_parquet(self.split_path, name_function=name_function)

        with Path.open(self.output_path / "limits.yaml", "w") as outfile:
            yaml.dump(limits, outfile, default_flow_style=False)

    def run(self) -> None:
        """Run the stratification and splitting step."""
        data_df = self.read()
        folds, metadata_df = self.transform(data_df)
        self.write(folds, metadata_df)
