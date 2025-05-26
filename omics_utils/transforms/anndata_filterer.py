from abc import abstractmethod

import anndata as ad

from omics_utils.utils.columns import ColumnNames


class AnnDataFilterer:
    """Apply a set of filters to an `AnnData` object."""

    def __init__(self, genes: list[str] | None, obs_filters: dict[str, list]) -> None:
        """
        Args:
            genes: Which genes to keep.
            obs_filters: Filters to apply to the `obs` `DataFrame` as a mapping from column to allowed values.
        """  # noqa: D212
        self.obs_filters = obs_filters
        self.genes = genes

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

        cell_filter = True
        for obs_col, obs_values in self.obs_filters.items():
            cell_filter &= adata.obs[obs_col].isin(obs_values)

        if self.genes is not None:
            gene_filter = adata.var.index.isin(self.genes)
            adata = adata[cell_filter, gene_filter].copy()
        else:
            adata = adata[cell_filter, :].copy()

        return adata
