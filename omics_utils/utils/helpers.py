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
