import uuid
from pathlib import Path

import anndata
import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp

from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import densify_matrix, sanitize_dtypes, sparsify_matrix
from omics_utils.utils.serialization import deserialize_sparse_matrix, serialize_sparse_matrix


class AnndataConverter:
    """
    Converter between AnnData objects and DataFrames with serialized sparse matrices.

    NOTE: This class only keeps ``X``, ``obs`` and ``var_names``, everything else will be discarded.

    """


    def __init__(
        self,
        obs_cols: list[str],
        var_cols: list[str] | None = None,
        var_cols_file: str | None = None,
        sparse: bool = True,
    ) -> None:
        """
        Initialize the converter.

        Args:
            obs_cols (list[str]): Columns to retain from the ``obs`` ``DataFrame``. E.g. sample-level metadata.
            var_cols (list[str]): Data columns to retain from the ``X`` array. E.g. genes. Inserts columns which are in 
this list but not in the data as empty columns.
            var_cols_file (str): Path to a csv file to load the column names from. The file should contain the names 
separated by new lines.
    	    sparse (bool): Whether to save the samples in a sparse format or as a dense ``DataFrame``
	"""
        if var_cols is not None and var_cols_file is not None:
            raise ValueError(
                "Cannot provide the ``var_cols`` and load ``var_cols_file`` at the same time. One option has to be None."
            )

        if var_cols_file is not None:
            if not Path(var_cols_file).exists():
                raise ValueError(f"The given {var_cols_file=} does not exist.")

            var_cols = (
                pd.read_csv(var_cols_file, header=None, index_col=None, names=["name"])["name"].to_numpy().tolist()
            )

        self.sparse = sparse
        self.obs_cols = obs_cols
        self.var_cols = var_cols

    def anndata_to_dataframe(self, adata: anndata.AnnData) -> pd.DataFrame:
	"""
	Convert an AnnData object to a DataFrame.

	The result will have all obs metadata plus a 'sparse_vector' column
	containing the serialized expression data for each cell.

	Args:
    	    adata (): AnnData object to convert

	Returns:
    	    ``DataFrame`` with cell metadata and serialized expression data: None
	"""
        adata.obs = self._prepare_metadata(adata)

        if self.var_cols is not None:
            adata = self.reindex_anndata_genes(adata, self.var_cols)

        if self.sparse:
            sparse_vectors = [serialize_sparse_matrix(x) for x in adata.X]
            df = pd.DataFrame({ColumnNames.SPARSE_VECTOR: sparse_vectors}, index=adata.obs_names).astype(str)
        else:
            X = densify_matrix(adata.X) if isinstance(adata.X, sp.spmatrix) else adata.X
            df = pd.DataFrame(X, index=adata.obs_names, columns=adata.var_names)

            if self.var_cols is not None:
                df = df.reindex(columns=self.var_cols).astype(float)

        df = df.join(adata.obs[[ColumnNames.CASE_ID, ColumnNames.SAMPLE_ID, *self.obs_cols]].astype(str))

        return df

    def dataframe_to_anndata(self, df: pd.DataFrame) -> anndata.AnnData:
       	"""
 	Convert a DataFrame back to an AnnData object.

	Args:
    	    df (pd.DataFrame): DataFrame with serialized expression data

	Returns:
    	    Reconstructed AnnData object: None
	"""
        id_cols = {ColumnNames.CASE_ID, ColumnNames.FOLD, ColumnNames.SAMPLE_ID}

        var_cols = self.var_cols if self.var_cols is not None else list(set(df.columns) - set(self.obs_cols) - id_cols)
        var = pd.DataFrame(index=var_cols)

        obs_cols = list(set(self.obs_cols) | id_cols)
        obs = sanitize_dtypes(df[obs_cols]).set_index(ColumnNames.SAMPLE_ID)

        if self.sparse:
            if ColumnNames.SPARSE_VECTOR not in df.columns:
                raise ValueError(
                    f"When using the sparse format, the `DataFrame` has to contain a column named "
                    f"`{ColumnNames.SPARSE_VECTOR}`."
                )

            sparse_rows = [deserialize_sparse_matrix(row) for row in df[ColumnNames.SPARSE_VECTOR]]
            X = sp.vstack(sparse_rows, format="csr")
        else:
            X = sparsify_matrix(df[var_cols].to_numpy(dtype=float))

        return anndata.AnnData(X=X, obs=obs, var=var)

    def _prepare_metadata(self, adata: ad.AnnData) -> pd.DataFrame:
	"""
	Prepare the metadata by renaming the columns and adding additional identifiers.

	Args:
    	    adata (ad.AnnData): The ``AnnData`` object to extract the metadata from.

	Returns:
    	    The metadata as a ``DataFrame``.: None
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
        """
	Reindex AnnData to exactly match a gene list while preserving sparsity.

	Args:
    	    adata (ad.AnnData): AnnData object to reindex
            genes (list[str]): List of gene names to enforce

	Returns:
    	    New AnnData with exactly the genes specified, in the specified order.: None
	"""
        n_cells = adata.n_obs
        n_genes = len(genes)

        common_genes = list(set(genes) & set(adata.var_names))
        old_indices = [adata.var_names.get_loc(g) for g in common_genes]
        new_indices = [genes.index(g) for g in common_genes]

        if not common_genes:
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

        return ad.AnnData(
            X=new_X,
            obs=adata.obs,
            var=adata.var.reindex(genes),
        )

