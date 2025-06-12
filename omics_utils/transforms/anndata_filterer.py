import anndata as ad

from omics_utils.utils.columns import ColumnNames


class AnnDataFilterer:
    """Apply a set of filters to an `AnnData` object."""

    def __init__(
        self,
        genes: list[str] | None,
        obs_filters: dict[str, list] | None = None,
        obs_col_renames: dict[str, str] | None = None,
    ) -> None:
        """
        Args:
            genes: Which genes to keep.
            obs_filters: Filters to apply to the `obs` `DataFrame` as a mapping from column to allowed values.
            obs_col_renames: Mapping of column renames in the `obs` `DataFrame`.
        """  # noqa: D212
        self.genes = genes
        self.obs_filters = obs_filters
        self.obs_col_renames = obs_col_renames

    def __call__(self, adata: ad.AnnData, batch_id: str) -> ad.AnnData:
        """Apply gene and cell filters an `AnnData` object.

        Args:
            adata: `AnnData` object to filter.
            batch_id: Batch identifier for the `AnnData` object.

        Returns:
        The filtered `AnnData` object.
        """
        if self.obs_col_renames is not None:
            adata.obs = adata.obs.rename(columns=self.obs_col_renames)

        adata.obs[ColumnNames.BATCH_ID] = batch_id

        cell_filter = [True] * len(adata)
        if self.obs_filters is not None:
            for obs_col, obs_values in self.obs_filters.items():
                cell_filter &= adata.obs[obs_col].isin(obs_values)

        if self.genes is not None:
            gene_filter = adata.var.index.isin(self.genes)
            adata = adata[cell_filter, gene_filter].copy()
        else:
            adata = adata[cell_filter, :].copy()

        return adata
