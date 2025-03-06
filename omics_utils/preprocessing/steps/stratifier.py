from pathlib import Path
from typing import Any

import anndata as ad
import dask.dataframe as dd
import pandas as pd
import scipy.sparse as sp
import yaml

from omics_utils.preprocessing.steps.step import Step
from omics_utils.splitting.splitter import Splitter
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import global_reset_index, sanitize_dtypes
from omics_utils.utils.serialization import deserialize_sparse_matrix


class Stratifier(Step):
    """Preprocessing step which reads case metadata, performs stratification and splits the data accordingly."""

    def __init__(
        self,
        *args,
        splitter: Splitter,
        metadata_columns: list[str],
        seed: int,
        partition_size: str = "10GB",
        **kwargs,
    ) -> None:
        """Args:
        ----
          splitter: Splitter to use for stratification, grouping and shuffling among folds.
          metadata_columns: List of columns that should be extracted as metadata from the `DataFrame`.
          seed: Seed to use for shuffling of the dataset.
          partition_size: The size of the resulting partitions in MB/GB. Should not be larger than memory.
        """
        super().__init__(*args, **kwargs)

        metadata_path = self.output_path / "metadata.parquet"
        split_path = self.output_path / "split"

        self.splitter = splitter
        self.metadata_columns = metadata_columns
        self.seed = seed
        self.partition_size = partition_size
        self.metadata_path = metadata_path
        self.split_path = split_path

    @property
    def input_step(self) -> str:
        """Name of the preceding preprocessing step."""
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
        for fold_idx in range(self.splitter.n_splits):
            fold_df = joined_df[joined_df[ColumnNames.FOLD] == fold_idx].sample(frac=1, random_state=self.seed)
            fold_df = global_reset_index(fold_df).compute_current_divisions(set_divisions=True)
            folds[fold_idx] = fold_df

        return folds, metadata_df

    def df_to_anndata(
        self, df: pd.DataFrame, output_dir: Path, fold_idx: int, partition_info: dict[str, Any] | None = None
    ) -> None:
        """Write a `DataFrame` to an anndata file.

        Args:
        ----
          df: Partition as a pandas `DataFrame` to save as an anndata file.
          output_dir: Folder to save the anndata file in.
          fold_idx: Index of the fold the partition belongs to.
          partition_info: Dictionary containing metadata about the partition.
        """
        part = partition_info["number"]

        gene_cols = list(set(df.columns) - set(self.metadata_columns) - {ColumnNames.CASE_ID, ColumnNames.FOLD})
        obs_cols = list(set(self.metadata_columns) | {ColumnNames.CASE_ID, ColumnNames.FOLD, ColumnNames.SAMPLE_ID})

        gene_df = df[gene_cols].set_index(ColumnNames.SAMPLE_ID)
        obs_df = sanitize_dtypes(df[obs_cols]).set_index(ColumnNames.SAMPLE_ID)

        x_matrix = sp.vstack([deserialize_sparse_matrix(r) for r in gene_df["cells"]], format="csr")
        # x_matrix = sparsify_matrix(gene_df.to_numpy(dtype=float))

        adata = ad.AnnData(X=x_matrix, obs=obs_df)
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

        with Path.open(self.output_path / "limits.yaml", "w") as outfile:
            yaml.dump(limits, outfile, default_flow_style=False)

    def run(self) -> None:
        """Run the stratification and splitting step."""
        data_df = self.read()
        folds, metadata_df = self.transform(data_df)
        self.write(folds, metadata_df)
