from abc import ABC, abstractmethod
from pathlib import Path

import dask.dataframe as dd
import pandas as pd

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.pipeline.step import Step
from omics_utils.utils.columns import ColumnNames


class Preprocessing(Step, ABC):
    """Base class for preprocessing of `AnnData` files."""

    def __init__(
        self,
        *args,
        converter: AnndataConverter,
        input_dir: str,
        n_inner_partitions: int = 10,
        n_debug: int | None = None,
        **kwargs,
    ) -> None:
        """
        Args:
            converter: Converter used to transform AnnData objects into DataFrames and the other way around.
            input_dir: Folder where the input `AnnData` files are saved.
            n_inner_partitions: Number of output partitions within each outer partition.
            n_debug: Take the first n input files only for debugging purposes.
        """  # noqa: D212
        super().__init__(*args, **kwargs)
        input_path = Path(input_dir)

        if not input_path.exists():
            raise ValueError("Input path does not exist.")

        self.converter = converter
        self.input_path = input_path
        self.n_inner_partitions = n_inner_partitions
        self.n_debug = n_debug

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

    @abstractmethod
    def read(self, input_files: list[Path]) -> dd.DataFrame:
        """Read and transform the data from the the input data.

        Args:
            input_files: File paths to process in parallel.

        Returns:
            The data ready for transformation.
        """
        ...

    @abstractmethod
    def transform(self, file_path: Path) -> pd.DataFrame:
        """Transform a single `AnnData` file."""
        ...

    @abstractmethod
    def write(self, data_df: dd.DataFrame) -> None:
        """Load/save the result of the transformation.

        Args:
            data_df: A `DataFrame` containing the patient/donor metadata and the serialized rows of `X`.
        """
        ...

    @abstractmethod
    def run(self) -> None:
        """Run the whole preprocessing step (read, transform and write)."""
        ...
