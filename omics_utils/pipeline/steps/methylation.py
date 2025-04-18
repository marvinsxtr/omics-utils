import uuid
from pathlib import Path

import anndata as ad
import dask.dataframe as dd
import pandas as pd

from omics_utils.pipeline.steps.preprocessing import Preprocessing
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import remove_empty_partitions


class MethylationPreprocessing(Preprocessing):
    """Preprocessing of DNA methylation array `AnnData` files."""

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

        data_df = dd.from_map(self.transform, input_files)
        data_df = remove_empty_partitions(data_df)
        return data_df

    def transform(self, file_path: Path) -> pd.DataFrame:
        """Preprocess a single `AnnData` file. Since the methylation array data are already preprocessed, this only
        adjusts column spelling.

        Returns:
            The preprocessed data as a pandas `DataFrame`.
        """
        adata = ad.read_h5ad(file_path)
        adata.obs = adata.obs.rename(columns={"sample_ID": ColumnNames.SAMPLE_ID})
        return self.converter.anndata_to_dataframe(adata)

    def write(self, data_df: dd.DataFrame) -> None:
        """Load/save the result of the transformation.

        Args:
            data_df: A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        data_df.repartition(npartitions=self.n_inner_partitions, force=True).to_parquet(
            self.output_path, filesystem="arrow", name_function=lambda _: f"{uuid.uuid4()!s}.parquet"
        )

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read` and `write`."""
        input_files = list(self.input_path.glob("*.h5ad"))
        data_df = self.read(input_files)
        self.write(data_df)
