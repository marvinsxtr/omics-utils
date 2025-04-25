import uuid

import anndata
import anndata as ad
import dask
import dask.array as da
import numpy as np
import pandas as pd
import scipy.sparse as sp
from dask.delayed import Delayed

from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import sanitize_dtypes
from omics_utils.utils.serialization import deserialize_sparse_matrix, serialize_sparse_matrix


class AnnDataConverter:
    """Converter between `AnnData` objects and `DataFrames` with serialized sparse matrices.

    NOTE: This class only keeps `X`, `obs` and `var_names`, everything else will be discarded.
    """

    def __init__(
        self,
        obs_cols: list[str],
        var_cols: list[str] | None = None,
    ) -> None:
        """
        Args:
            obs_cols: Columns to retain from the `obs` `DataFrame`, e.g. sample-level metadata
            var_cols: Data columns to retain from the `X` array, e.g. genes. Inserts columns which are
                in this list but not in the data as empty columns.
        """  # noqa: D212
        self.obs_cols = obs_cols
        self.var_cols = var_cols

    def serialize(self, adata: ad.AnnData) -> list[Delayed]:
        """Serialize a Dask-backed `AnnData` object.

        Args:
            adata: The `AnnData` object to serialize.

        Returns:
            A list of `Delayed` tasks computing the serialized entries from the `AnnData` object.
        """

        def serialize_partition(block: sp.csr_matrix, obs_names_part: list[str], obs: pd.DataFrame) -> pd.DataFrame:
            """Serialize a partition of data."""
            sparse_vectors = [serialize_sparse_matrix(row) for row in block]
            df = pd.DataFrame({ColumnNames.SPARSE_VECTOR: sparse_vectors}, index=obs_names_part)
            return self.join_metadata(df, obs)

        X_dask = adata.X
        obs_names = adata.obs_names
        offsets = np.cumsum((0,) + X_dask.chunks[0])

        arrays = [X_dask[offsets[i] : offsets[i + 1]] for i in range(len(X_dask.chunks[0]))]
        names = [obs_names[offsets[i] : offsets[i + 1]] for i in range(len(X_dask.chunks[0]))]

        return [dask.delayed(serialize_partition)(a, n, adata.obs) for a, n in zip(arrays, names, strict=False)]

    def join_metadata(self, df: pd.DataFrame, obs: pd.DataFrame) -> pd.DataFrame:
        """Join the observation metadata and IDs to the main `DataFrame`.

        Args:
            df: `DataFrame` containing the cells as serialized strings.
            obs: `DataFrame` containing `AnnData.obs`.

        Returns:
            The joined `DataFrame`.
        """
        return df.join(
            obs[[ColumnNames.CASE_ID, ColumnNames.SAMPLE_ID, ColumnNames.BATCH_ID, *self.obs_cols]].astype(str)
        )

    def anndata_to_dataframe(self, adata: anndata.AnnData) -> list[Delayed]:
        """Convert an AnnData object to a DataFrame.

        The result will have all obs metadata plus a `sparse_vector` column
        containing the serialized expression data for each cell.

        Args:
            adata: `AnnData` object to convert

        Returns:
        List of `Delayed` serialization tasks.
        """
        adata.obs = self._prepare_metadata(adata)

        if self.var_cols is not None and adata.n_obs > 0:
            adata = self.reindex_anndata_genes(adata, self.var_cols)

        if not isinstance(adata.X, da.Array):
            raise TypeError("AnnData object must contain a dask-backed `X`.")

        if adata.n_obs == 0:
            return []

        return self.serialize(adata)

    def dataframe_to_anndata(self, df: pd.DataFrame) -> anndata.AnnData:
        """Convert a `DataFrame` back to an `AnnData` object.

        Args:
            df: `DataFrame` with serialized expression data

        Returns:
            Reconstructed `AnnData` object.
        """
        id_cols = {ColumnNames.CASE_ID, ColumnNames.SAMPLE_ID, ColumnNames.BATCH_ID}

        var_cols = self.var_cols if self.var_cols is not None else list(set(df.columns) - set(self.obs_cols) - id_cols)
        var = pd.DataFrame(index=var_cols)

        obs_cols = list(set(self.obs_cols) | id_cols)
        obs = sanitize_dtypes(df[obs_cols]).set_index(ColumnNames.SAMPLE_ID)

        if ColumnNames.SPARSE_VECTOR not in df.columns:
            raise ValueError(f"The `DataFrame` has to contain a column named `{ColumnNames.SPARSE_VECTOR}`.")

        sparse_rows = [deserialize_sparse_matrix(row) for row in df[ColumnNames.SPARSE_VECTOR]]
        X = sp.vstack(sparse_rows, format="csr")

        return anndata.AnnData(X=X, obs=obs, var=var)

    def _prepare_metadata(self, adata: ad.AnnData) -> pd.DataFrame:
        """Prepare the metadata by renaming the columns and adding additional identifiers.

        Args:
            adata: The `AnnData` object to extract the metadata from

        Returns:
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
        """Reindex `AnnData` to exactly match a gene list while preserving sparsity.

        Args:
            adata: `AnnData` object to reindex
            genes: List of gene names to enforce

        Returns:
            New `AnnData` object with exactly the genes specified, in the specified order.
        """
        if adata.n_obs == 0:
            raise ValueError("Must have at least one observation to reindex the genes.")

        if not isinstance(adata.X, da.Array):
            raise TypeError("AnnData object must contain a dask-backed `X`.")

        n_genes = len(genes)
        common_genes = list(set(genes) & set(adata.var_names))

        old_indices = np.array([adata.var_names.get_loc(g) for g in common_genes])
        new_indices = np.array([genes.index(g) for g in common_genes])

        P = sp.csr_matrix((np.ones(len(common_genes)), (old_indices, new_indices)), shape=(adata.n_vars, n_genes))

        return ad.AnnData(
            adata.X.dot(P),
            obs=adata.obs,
            var=adata.var.reindex(genes),
        )
