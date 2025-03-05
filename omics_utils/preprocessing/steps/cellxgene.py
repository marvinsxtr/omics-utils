from pathlib import Path

import anndata as ad
import pandas as pd
import scanpy as sc

from omics_utils.preprocessing.steps.preprocessing import Preprocessing
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import densify_matrix


class CellXGenePreprocessing(Preprocessing):
    """Preprocessing of CellXGene `AnnData` files."""

    def __init__(
        self,
        *args,
        input_dir: str,
        gene_vocab_file: str,
        n_debug: int | None = None,
        metadata_columns: list[str] | None = None,
        **kwargs,
    ) -> None:
        """Args:
        ----
          input_dir: Folder where the input CellXGene `AnnData` files are saved.
          gene_vocab_file: Path to the gene vocabulary to filter by.
          n_debug: Take the first n input files only for debugging purposes.
          metadata_columns: List of columns in `AnnData.obs` that are considered metadata.
                            If None, defaults to ["sex", "tissue", "disease", "assay"].
        """
        super().__init__(*args, input_dir=input_dir, metadata_columns=metadata_columns, n_debug=n_debug, **kwargs)

        gene_vocab_path = Path(gene_vocab_file)

        if not gene_vocab_path.exists():
            raise ValueError("Gene vocab path does not exist.")

        self.gene_vocab = (
            pd.read_csv(gene_vocab_path, header=None, index_col=None, names=["name"])["name"].to_numpy().tolist()
        )
        self.gene_vocab_path = gene_vocab_path

    def transform(self, file_path: Path) -> pd.DataFrame:
        """Preprocess a single `AnnData` file.

        Args:
        ----
          file_path: Path to the `AnnData` file to be transformed.

        Returns:
        -------
        The preprocessed data as a pandas `DataFrame`.
        """
        adata = ad.read_h5ad(file_path)

        # Define X to be the raw counts
        if hasattr(adata, "raw") and hasattr(adata.raw, "X"):
            if adata.var.shape[0] != adata.raw.var.shape[0]:
                raise ValueError("Number of raw variables has to match the number of preprocessed variables.")
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
        gene_filter = adata.var.index.isin(self.gene_vocab)

        # Filter cells and genes
        adata = adata[cell_filter, gene_filter].copy()

        # Check if all cells/genes were filtered out
        if adata.n_obs == 0 or adata.n_vars == 0:
            return self.anndata_to_df(adata)

        # Preprocessing
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)

        return self.anndata_to_df(adata)

    def anndata_to_df(self, adata: ad.AnnData) -> pd.DataFrame:
        """Convert a CellXGene `AnnData` file to a pandas `DataFrame` containing `X` and the metadata.

        Args:
        ----
          adata: The already preprocessed `AnnData` object to be converted.

        Returns:
        -------
        A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        adata.obs = self._prepare_metadata(adata)

        X = densify_matrix(adata.X)

        df = pd.DataFrame(X, index=adata.obs_names, columns=adata.var_names)
        df = df.reindex(columns=self.gene_vocab).astype(float)
        df = df.join(adata.obs[[ColumnNames.CASE_ID, ColumnNames.SAMPLE_ID, *self.metadata_columns]].astype(str))

        return df
