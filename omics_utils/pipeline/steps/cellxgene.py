from pathlib import Path

import anndata as ad
import pandas as pd
import scanpy as sc

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.pipeline.steps.preprocessing import Preprocessing
from omics_utils.utils.columns import ColumnNames


class CellXGenePreprocessing(Preprocessing):
    """Preprocessing of CellXGene ``AnnData`` files."""

    def __init__(
        self,
        *args,
        input_dir: str,
        converter: AnndataConverter,
        n_debug: int | None = None,
        **kwargs,
    ) -> None:
        """Initializes an instance of a preprocessing step for CellXGene files.

        Args:
            *args: TODO
            input_dir (str ): Folder where the input CellXGene ``AnnData`` files are saved.
            converter (AnndataConverter): Converter to convert ``AnnData`` into a ``DataFrame`` format.
            n_debug (): Take the first n input files only for debugging purposes.
            **kwargs: TODO
        """
        super().__init__(*args, converter=converter,
                         input_dir=input_dir, n_debug=n_debug, **kwargs)

    def transform(self, file_path: Path) -> pd.DataFrame:
        """Preprocess a single ``AnnData`` file.

        Args:
            file_path (Path): Path to the ``AnnData`` file to be transformed.

        Returns:
            The preprocessed data as a pandas ``DataFrame``.
        """
        adata = ad.read_h5ad(file_path)

        # Correct column spelling
        adata.obs = adata.obs.rename(columns={"donor_id": ColumnNames.CASE_ID})

        # Define X to be the raw counts
        if hasattr(adata, "raw") and hasattr(adata.raw, "X"):
            if adata.var.shape[0] != adata.raw.var.shape[0]:
                raise ValueError(
                    "Number of raw variables has to match the number of preprocessed variables.")
            adata.X = adata.raw.X
        elif ((adata.X.astype("int") != adata.X).nnz != 0) and ((adata.X < 0).nnz == 0):
            raise ValueError("X has to contain raw expression counts.")

        # Filter out non-human tissue, non-primary and diseased data
        cell_filter = (
            (adata.obs["organism_ontology_term_id"] == "NCBITaxon:9606")
            & (adata.obs["is_primary_data"] == True)
            & (adata.obs["disease"] == "normal")
            & (
                adata.obs["assay"].isin(
                    [
                        "10x 3' v1",
                        "10x 3' v2",
                        "10x 3' v3",
                        "10x 5' v1",
                        "10x 5' v2",
                        "10x 3' transcription profiling",
                        "10x 5' transcription profiling",
                    ]
                )
            )
        )

        # Only use genes in vocabulary
        gene_filter = adata.var.index.isin(self.converter.var_cols)

        # Filter cells and genes
        adata = adata[cell_filter, gene_filter].copy()

        # Check if all cells/genes were filtered out
        if adata.n_obs == 0 or adata.n_vars == 0:
            return self.converter.anndata_to_dataframe(adata)

        # Preprocessing
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)

        return self.converter.anndata_to_dataframe(adata)
