from pathlib import Path

import anndata as ad
import h5py
import pandas as pd

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.pipeline.steps.preprocessing import Preprocessing
from omics_utils.utils.columns import ColumnNames


class CellXGenePreprocessing(Preprocessing):
    """Preprocessing of CellXGene `AnnData` files."""

    def __init__(
        self,
        *args,
        input_dir: str,
        converter: AnndataConverter,
        n_debug: int | None = None,
        chunk_size: int = 25000,
        **kwargs,
    ) -> None:
        """Args:
        ----
          input_dir: Folder where the input CellXGene `AnnData` files are saved.
          converter: Converter to convert `AnnData` into a `DataFrame` format.
          gene_vocab_file: Path to the gene vocabulary to filter by.
          n_debug: Take the first n input files only for debugging purposes.
          chunk_size: Chunk size of the expression matrix in dask.
        """
        super().__init__(*args, converter=converter, input_dir=input_dir, n_debug=n_debug, **kwargs)
        self.chunk_size = chunk_size

    def transform(self, file_path: Path) -> pd.DataFrame:
        """Preprocess a single `AnnData` file.

        Args:
        ----
          file_path: Path to the `AnnData` file to be transformed.

        Returns:
        -------
        The preprocessed data as a pandas `DataFrame`.
        """
        with h5py.File(file_path, "r") as f:
            adata = ad.AnnData(
                obs=ad.io.read_elem(f["obs"]),
                var=ad.io.read_elem(f["var"]),
            )
            adata.X = ad.experimental.read_elem_as_dask(
                f["raw/X"] if "raw/X" in f else f["X"], chunks=(self.chunk_size, adata.shape[1])
            )

        # Correct column spelling
        adata.obs = adata.obs.rename(columns={"donor_id": ColumnNames.CASE_ID})

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

        return self.converter.anndata_to_dataframe(adata)
