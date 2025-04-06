from pathlib import Path
from typing import Any

import dask.dataframe as dd
import pandas as pd
from anndata._io.h5ad import write_h5ad
from dask_ml.model_selection import train_test_split

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.pipeline.step import Step
from omics_utils.splitting.splitter import Splitter
from omics_utils.utils.columns import ColumnNames


class Stratifier(Step):
    """Preprocessing step which reads case metadata, performs stratification and splits the data accordingly."""

    def __init__(
        self,
        *args,
        splitter: Splitter,
        converter: AnndataConverter,
        seed: int,
        **kwargs,
    ) -> None:
        """
        Args:
            splitter: Splitter to use for stratification, grouping and shuffling among folds.
            converter: Converter used to convert the `DataFrame` format back to `AnnData`.
            seed: Seed to use for shuffling of the dataset.
        """  # noqa: D212
        super().__init__(*args, **kwargs)

        metadata_path = self.output_path / "metadata.parquet"
        split_path = self.output_path / "split"

        self.splitter = splitter
        self.converter = converter
        self.seed = seed
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

        Returns:
            The data ready for transformation.
        """
        return dd.read_parquet(
            list(self.input_path.glob("*.parquet")), split_row_groups=True, ignore_metadata_file=True
        )

    def transform(self, data_df: dd.DataFrame) -> tuple[dict[int, dd.DataFrame], pd.DataFrame]:
        """Extract the metadata and perform splitting.

        Returns:
            A tuple of a dict containing a mapping of the fold index to the data split and the metadata `DataFrame`.
        """
        metadata_df: pd.DataFrame = (
            data_df[[ColumnNames.CASE_ID, *self.converter.obs_cols]].drop_duplicates().reset_index(drop=True).compute()
        )
        metadata_df = metadata_df.set_index(ColumnNames.CASE_ID)
        metadata_df.to_parquet(self.metadata_path)

        data_df = data_df.sort_values(ColumnNames.SAMPLE_ID, npartitions=500)

        train_df, val_df = train_test_split(data_df, test_size=0.1, random_state=self.seed, shuffle=False)
        return train_df, val_df, metadata_df

    def write_df_to_anndata(
        self, df: pd.DataFrame, output_dir: Path, fold_idx: int, partition_info: dict[str, Any] | None = None
    ) -> None:
        """Write a `DataFrame` to an anndata file.

        Args:
            df: Partition as a pandas `DataFrame` to save as an AnnData `.h5ad` file.
            output_dir: Folder to save the anndata file in.
            fold_idx: Index of the fold the partition belongs to.
            partition_info: Dictionary containing metadata about the partition.
        """
        part = partition_info["number"]
        adata = self.converter.dataframe_to_anndata(df)
        write_h5ad(output_dir / f"fold_{fold_idx}_part_{part}.h5ad", adata, convert_strings_to_categoricals=False)

    def write(self, train_df: dd.DataFrame, val_df: dd.DataFrame, metadata_df: pd.DataFrame) -> None:
        """Save the folds and the case metadata separately.

        Args:
            folds: A dict containing a mapping of the fold index to the data split.
            metadata_df: The metadata `DataFrame`.
        """
        metadata_df.to_parquet(self.metadata_path)
        self.split_path.mkdir(exist_ok=True)

        train_df.map_partitions(self.write_df_to_anndata, self.split_path, "train", meta=pd.DataFrame()).compute()
        val_df.map_partitions(self.write_df_to_anndata, self.split_path, "val", meta=pd.DataFrame()).compute()

    def run(self) -> None:
        """Run the stratification and splitting step."""
        data_df = self.read()
        train_df, val_df, metadata_df = self.transform(data_df)
        self.write(train_df, val_df, metadata_df)
