import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import anndata as ad
import dask.dataframe as dd
import pandas as pd

from omics_utils.preprocessing.steps.step import Step
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import remove_empty_partitions


class Preprocessing(Step, ABC):
    """Base class for preprocessing of `AnnData` files."""

    def __init__(
        self, *args, input_dir: str, metadata_columns: list[str], n_debug: int | None = None, **kwargs
    ) -> None:
        """Args:
        ----
          input_dir: Folder where the input `AnnData` files are saved.
          metadata_columns: List of columns in `AnnData.obs` that are considered metadata.
          n_debug: Take the first n input files only for debugging purposes.
        """
        super().__init__(*args, **kwargs)

        input_path = Path(input_dir)

        if not input_path.exists():
            raise ValueError("Input path does not exist.")

        self.input_path = input_path
        self.n_debug = n_debug
        self.metadata_columns = metadata_columns

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

        Returns
        -------
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
        """Transform a single `AnnData` file.

        Args:
        ----
          file_path: Path to the `AnnData` file to be transformed.

        Returns:
        -------
        The data as a pandas `DataFrame`.
        """
        ...

    def _prepare_metadata(self, adata: ad.AnnData) -> pd.DataFrame:
        """Prepare the metadata by renaming the columns and adding additional identifiers.

        Args:
        ----
          adata: The `AnnData` object to extract the metadata from.

        Returns:
        -------
        The metadata as a `DataFrame`.
        """
        obs = adata.obs

        # Assign additional sample identifiers
        if ColumnNames.SAMPLE_ID in obs.columns:
            obs["original_sample_id"] = obs[ColumnNames.SAMPLE_ID]

        obs[ColumnNames.SAMPLE_ID] = [str(uuid.uuid4()) for _ in range(len(adata.obs))]
        obs[ColumnNames.SAMPLE_ID] = obs[ColumnNames.SAMPLE_ID].astype(str)

        # If data does not contain a case_id, generate it from sample_id
        if ColumnNames.CASE_ID not in obs.columns:
            obs[ColumnNames.CASE_ID] = [str(uuid.uuid4()) for _ in range(len(obs))]
            obs[ColumnNames.CASE_ID] = obs[ColumnNames.CASE_ID].astype(str)
        else:
            obs[ColumnNames.CASE_ID] = (
                obs[ColumnNames.CASE_ID]
                .map({case_id: str(uuid.uuid4()) for case_id in obs[ColumnNames.CASE_ID].unique()})
                .astype(str)
            )

        obs = obs.set_index(ColumnNames.SAMPLE_ID, drop=False).rename_axis(None)

        return obs

    def anndata_to_df(self, adata: ad.AnnData) -> pd.DataFrame:
        """Convert an `AnnData` file to a pandas `DataFrame` containing `X` and the metadata.

        Args:
        ----
          adata: The already preprocessed `AnnData` object to be converted.

        Returns:
        -------
        A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        adata.obs = self._prepare_metadata(adata)

        df = pd.DataFrame(adata.X, index=adata.obs_names, columns=adata.var_names)
        df = df.join(adata.obs[[ColumnNames.CASE_ID, ColumnNames.SAMPLE_ID, *self.metadata_columns]].astype(str))

        return df

    def write(self, data_df: dd.DataFrame) -> None:
        """Load/save the result of the transformation.

        Args:
        ----
          data_df: A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        data_df.to_parquet(self.output_path, filesystem="arrow", name_function=lambda part: f"part_{part}.parquet")

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read` and `write`."""
        data_df = self.read()
        self.write(data_df)
