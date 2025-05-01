from abc import abstractmethod

import anndata as ad

from omics_utils.utils.columns import ColumnNames


class AnnDataFilterer:
    """Apply a set of filters to an `AnnData` object."""

    def __init__(self, var_cols: list[str] | None, only_primary: bool = True) -> None:
        """
        Args:
            var_cols: Which columns to keep.
            only_primary: Whether to only process cells marked as primary data.
        """  # noqa: D212
        self.only_primary = only_primary
        self.var_cols = var_cols

    @abstractmethod
    def __call__(self, adata: ad.AnnData, batch_id: str) -> ad.AnnData:
        """Apply the filters to an `AnnData` object.

        Args:
            adata: `AnnData` object to filter.
            batch_id: Batch identifier for the `AnnData` object.

        Returns:
        The filtered `AnnData` object.
        """
        ...


class CellXGeneFilterer(AnnDataFilterer):
    """Filters `AnnData` objects from the CellXGene dataset."""

    def __call__(self, adata: ad.AnnData, batch_id: str) -> ad.AnnData:
        """Apply gene and observation filters an `AnnData` object.

        Args:
            adata: `AnnData` object to filter.
            batch_id: Batch identifier for the `AnnData` object.

        Returns:
        The filtered `AnnData` object.
        """
        adata.obs = adata.obs.rename(columns={"donor_id": ColumnNames.CASE_ID})
        adata.obs[ColumnNames.BATCH_ID] = batch_id

        # Filter out non-human tissue, non-primary and diseased data
        cell_filter = (adata.obs["organism_ontology_term_id"] == "NCBITaxon:9606") & (
            adata.obs["assay"].isin(
                [
                    "10x transcription profiling",
                    "10x 3' transcription profiling",
                    "10x 3' v1",
                    "10x 3' v2",
                    "10x 3' v3",
                    "10x 3' v4",
                    "10x 5' transcription profiling",
                    "10x 5' v1",
                    "10x 5' v2",
                    "10x 5' v3",
                ]
            )
        )

        if self.only_primary:
            cell_filter = cell_filter & (adata.obs["is_primary_data"] == True)

        if self.var_cols is not None:
            gene_filter = adata.var.index.isin(self.var_cols)
            adata = adata[cell_filter, gene_filter].copy()
        else:
            adata = adata[cell_filter, :].copy()

        return adata
