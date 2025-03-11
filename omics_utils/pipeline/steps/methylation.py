from pathlib import Path

import anndata as ad
import pandas as pd

from omics_utils.pipeline.steps.preprocessing import Preprocessing
from omics_utils.utils.columns import ColumnNames


class MethylationPreprocessing(Preprocessing):
    """Preprocessing of DNA methylation array `AnnData` files."""

    def transform(self, file_path: Path) -> pd.DataFrame:
        """Preprocess a single `AnnData` file. Since the methylation array data are already preprocessed this only
        adjusts column spelling.

        Args:
        ----
          file_path: Path to the `AnnData` file to be transformed.

        Returns:
        -------
        The preprocessed data as a pandas `DataFrame`.
        """
        adata = ad.read_h5ad(file_path)

        # Correct column spelling
        adata.obs = adata.obs.rename(columns={"sample_ID": ColumnNames.SAMPLE_ID})

        return self.converter.anndata_to_dataframe(adata)
<<<<<<< HEAD
=======
      
>>>>>>> 85bfcca (Create methylation.py)
