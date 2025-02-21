import dask.dataframe as dd
import numpy as np
from scipy import sparse


def remove_empty_partitions(df: dd.DataFrame) -> dd.DataFrame:
    """Removes empty partitions from a dask `DataFrame`.

    Args:
    ----
      df: Dask `DataFrame` to remove empty partitions from.

    Returns:
    -------
    Dask `DataFrame` without empty partitions.
    """
    ll = list(df.map_partitions(len).compute())
    df_delayed = df.to_delayed()
    df_delayed_new = []
    pempty = None
    for ix, n in enumerate(ll):
        if n == 0:
            pempty = df.get_partition(ix)
        else:
            df_delayed_new.append(df_delayed[ix])
    if pempty is not None:
        df = dd.from_delayed(df_delayed_new, meta=pempty)
    return df


def densify_matrix(sparse_matrix: sparse.spmatrix) -> np.ndarray:
    """Replaces missing values with `np.nan` while preserving zeros.

    Args:
    ----
      sparse_matrix: The sparse matrix to densify, e.g. in csr format.

    Returns:
    -------
    The densified matrix.
    """
    dense = np.full(sparse_matrix.shape, np.nan)
    coo = sparse_matrix.tocoo()
    dense[coo.row, coo.col] = coo.data
    return dense


def sparsify_matrix(dense_matrix: np.ndarray) -> sparse.csr_matrix:
    """Convert a dense matrix to a sparse matrix where `np.nan` are not explicitly stored.

    Args:
    ----
      dense_matrix: Matrix to sparsify.

    Returns:
    -------
    The sparse matrix storing zeros explicitly and not storing `np.nan`.
    """
    mask = ~np.isnan(dense_matrix)
    rows, cols = np.nonzero(mask)
    values = dense_matrix[mask]
    sparse_matrix = sparse.csr_matrix((values, (rows, cols)), shape=dense_matrix.shape)
    return sparse_matrix


def global_reset_index(df: dd.DataFrame, index_name: str = None) -> dd.DataFrame:
    """Resets the index of a dask `DataFrame` globally instead of per partition.

    Args:
    ----
      df: Dask `DataFrame` to reset the index of.
      index_name: Name of the new index.

    Returns:
    -------
    Dask `DataFrame` with a globally reset index.
    """
    df = df.assign(tmp_idx=1)
    # Have to drop after resetting the index since the drop=True flag does not work
    df = df.set_index((df["tmp_idx"].cumsum() - 1).rename(index_name))
    df = df.drop(columns="tmp_idx")
    return df
