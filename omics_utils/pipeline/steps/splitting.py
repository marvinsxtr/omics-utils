import json
from pathlib import Path
from typing import Any

import dask
import dask.dataframe as dd
import pandas as pd
from anndata._io.h5ad import write_h5ad
from dask_ml.model_selection import train_test_split

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.pipeline.step import Step
from omics_utils.utils.columns import ColumnNames


class Splitting(Step):
    """Preprocessing step which reads case metadata and splits the data accordingly."""

    def __init__(
        self,
        *args,
        converter: AnndataConverter,
        seed: int,
        n_partitions: int,
        test_size: float = 0.1,
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
        categories_path = self.output_path / "categories.json"

        self.converter = converter
        self.seed = seed
        self.metadata_path = metadata_path
        self.split_path = split_path
        self.n_partitions = n_partitions
        self.test_size = test_size
        self.categories_path = categories_path

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

        categorized_df = data_df.categorize(columns=self.converter.obs_cols)
        categories = {col: list(categorized_df[col].cat.categories) for col in self.converter.obs_cols}

        with Path.open(self.categories_path, "w") as file:
            json.dump(categories, file)

        data_df = data_df.drop_duplicates(subset=ColumnNames.SAMPLE_ID)
        data_df = data_df.sort_values(ColumnNames.SAMPLE_ID, npartitions=self.n_partitions)

        train_df, val_df = train_test_split(data_df, test_size=self.test_size, random_state=self.seed, shuffle=False)
        return train_df, val_df, metadata_df

    def write_df_to_anndata(
        self, df: pd.DataFrame, output_dir: Path, fold_name: str, partition_info: dict[str, Any] | None = None
    ) -> None:
        """Write a `DataFrame` to an anndata file.

        Args:
            df: Partition as a pandas `DataFrame` to save as an AnnData `.h5ad` file.
            output_dir: Folder to save the anndata file in.
            fold_name: Name of the fold the partition belongs to. Usually train or val.
            partition_info: Dictionary containing metadata about the partition.
        """
        part = partition_info["number"]
        adata = self.converter.dataframe_to_anndata(df)
        write_h5ad(output_dir / f"fold_{fold_name}_part_{part}.h5ad", adata, convert_strings_to_categoricals=False)

    def write(self, train_df: dd.DataFrame, val_df: dd.DataFrame, metadata_df: pd.DataFrame) -> None:
        """Save the folds and the case metadata separately.

        Args:
            folds: A dict containing a mapping of the fold index to the data split.
            metadata_df: The metadata `DataFrame`.
        """
        metadata_df.to_parquet(self.metadata_path)
        self.split_path.mkdir(exist_ok=True)

        train_task = train_df.map_partitions(self.write_df_to_anndata, self.split_path, "train", meta=pd.DataFrame())
        val_task = val_df.map_partitions(self.write_df_to_anndata, self.split_path, "val", meta=pd.DataFrame())

        dask.compute(train_task, val_task)

    def run(self) -> None:
        """Run the stratification and splitting step."""
        data_df = self.read()
        train_df, val_df, metadata_df = self.transform(data_df)
        self.write(train_df, val_df, metadata_df)
