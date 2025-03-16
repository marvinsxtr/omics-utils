from abc import ABC, abstractmethod
from pathlib import Path

import dask.dataframe as dd
import pandas as pd

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.pipeline.step import Step
from omics_utils.utils.helpers import remove_empty_partitions


class Preprocessing(Step, ABC):
    """Base class for preprocessing of ``AnnData`` files."""

    def __init__(
        self, *args, converter: AnndataConverter, input_dir: str, n_debug: int | None = None, **kwargs
    ) -> None:
        """Initializes an instance of a preprocessing object with custom-chosen steps.
        
        Args:
            input_dir: Folder where the input ``AnnData`` files are saved.
            n_debug: Take the first n input files only for debugging purposes.
        """
        super().__init__(*args, **kwargs)
        input_path = Path(input_dir)

        if not input_path.exists():
            raise ValueError("Input path does not exist.")

        self.converter = converter
        self.input_path = input_path
        self.n_debug = n_debug

    @property
    def input_step(self) -> str | None:
        """Has no preceding preprocessing step."""
        return None

    @property
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        return "data"

    def read(self) -> dd.DataFrame:
        """Read and transform the data from the the input data.

        NOTE: In this case the read step contains the transform step for compatibility with dask.


        Returns:
            The data ready for transformation.
        """
        input_files = list(self.input_path.glob("*.h5ad"))

        if self.n_debug is not None:
            input_files = input_files[: self.n_debug]

        data_df = dd.from_map(self.transform, input_files)
        data_df = remove_empty_partitions(data_df)
        return data_df

    @abstractmethod
    def transform(self, file_path: Path) -> pd.DataFrame:
        """Transform a single ``AnnData`` file."""
        ...

    def write(self, data_df: dd.DataFrame) -> None:
        """Load/save the result of the transformation.

        Args:
            data_df (): A ``DataFrame`` containing the patient/donor metadata and the matrix ``X``.
        """
        data_df.to_parquet(self.output_path, filesystem="arrow", name_function=lambda part: f"part_{part}.parquet")

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running ``read`` and ``write``."""
        data_df = self.read()
        self.write(data_df)      

