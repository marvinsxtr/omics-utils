from pathlib import Path

import dask.dataframe as dd
import pandas as pd
import yaml

from omics_utils.preprocessing.steps.step import PreprocessingStep
from omics_utils.splitting.splitter import Splitter
from omics_utils.utils.columns import ColumnNames


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
            fold_df: dd.DataFrame = (
                joined_df[joined_df[ColumnNames.FOLD] == fold_idx]
                .sample(frac=1)
                .repartition(partition_size=self.partition_size, force=True)
                .reset_index()
                .compute_current_divisions(set_divisions=True)
            )
            folds[fold_idx] = fold_df

        return folds, metadata_df

    def write(self, folds: dict[int, dd.DataFrame], metadata_df: pd.DataFrame) -> None:
        """Save the folds and the case metadata separately.

        Args:
        ----
          folds: A dict containing a mapping of the fold index to the data split.
          metadata_df: The metadata `DataFrame`.
        """
        metadata_df.to_parquet(self.metadata_path)

        self.split_path.mkdir(exist_ok=True)

        divisions = {}
        for fold_idx, fold_df in folds.items():

            def name_function(part: int) -> str:
                return f"fold_{fold_idx}_part_{part}.parquet"  # noqa: B023

            divisions[fold_idx] = list(fold_df.divisions)

            fold_df.to_parquet(self.split_path, name_function=name_function)

        with Path.open(self.output_path / "divisions.yaml", "w") as outfile:
            yaml.dump(divisions, outfile, default_flow_style=False)

    def run(self) -> None:
        """Run the stratification and splitting step."""
        data_df = self.read()
        folds, metadata_df = self.transform(data_df)
        self.write(folds, metadata_df)
