import uuid
from pathlib import Path

import anndata as ad
import dask.array as da
import h5py
import numpy as np
import pandas as pd
import scanpy as sc
import scipy.sparse as sp

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

        # Check if all cells/genes were filtered out
        if adata.n_obs == 0 or adata.n_vars == 0:
            return self.converter.anndata_to_dataframe(adata)

        # Preprocessing
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)

        adata.obs = self._prepare_metadata(adata)

        if self.converter.var_cols is not None:
            adata = self.reindex_anndata_genes(adata, self.converter.var_cols)

        return self.converter.anndata_to_dataframe(adata)

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

    def reindex_anndata_genes(self, adata: ad.AnnData, genes: list[str]) -> ad.AnnData:
        """Reindex AnnData to exactly match a gene list while preserving sparsity.

        Args:
        ----
        adata: AnnData object to reindex
        genes: List of gene names to enforce

        Returns:
        -------
        New AnnData with exactly the genes specified, in the specified order.
        """
        n_cells = adata.n_obs
        n_genes = len(genes)

        common_genes = list(set(genes) & set(adata.var_names))
        old_indices = [adata.var_names.get_loc(g) for g in common_genes]
        new_indices = [genes.index(g) for g in common_genes]

        if isinstance(adata.X, sp.csr_matrix):
            if len(common_genes) == 0:
                new_X = sp.csr_matrix((n_cells, n_genes), dtype=adata.X.dtype)
            else:
                coo = adata.X.tocoo()

                mask = np.isin(coo.col, old_indices)
                data = coo.data[mask]
                rows = coo.row[mask]
                cols = coo.col[mask]

                old_to_new = dict(zip(old_indices, new_indices, strict=True))
                mapped_cols = np.array([old_to_new[col] for col in cols])

                new_X = sp.csr_matrix((data, (rows, mapped_cols)), shape=(n_cells, n_genes))
        elif isinstance(adata.X, da.Array):
            new_X = da.zeros(
                (n_cells, n_genes), chunks=(self.chunk_size, adata.shape[1]), dtype=np.float32
            ).map_blocks(
                lambda x: sp.csr_matrix(x.shape, dtype=np.float32), meta=sp.csr_matrix((0, 0), dtype=np.float32)
            )
            if len(common_genes) > 0 and n_cells > 0:
                new_X[:, new_indices] = adata.X[:, old_indices]
        else:
            raise NotImplementedError(f"The type {type(adata.X)} is not supported.")

        return ad.AnnData(
            new_X,
            obs=adata.obs,
            var=adata.var.reindex(genes),
        )
