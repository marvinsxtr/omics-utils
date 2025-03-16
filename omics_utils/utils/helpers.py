from pathlib import Path

import dask.dataframe as dd
import numpy as np
import pandas as pd
import scipy.sparse as sp
from ml_project_template.common.utils.config import get_hydra_output_dir


def get_output_dir() -> Path:
    """Get the current output directory.

    Returns:
        Output path of the current run.
    """
    try:
        output_dir = get_hydra_output_dir()
    except ValueError:
        output_dir = Path("/tmp/outputs")
        output_dir.mkdir(exist_ok=True, parents=True)
    return output_dir


def remove_empty_partitions(df: dd.DataFrame) -> dd.DataFrame:
    """Removes empty partitions from a dask ``DataFrame``.

    Args:
        df (dd.DataFrame): Dask ``DataFrame`` to remove empty partitions from.

    Returns:
        Dask ``DataFrame`` without empty partitions.: None
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


def densify_matrix(sparse_matrix: sp.spmatrix) -> np.ndarray:
    """Replaces missing values with ``np.nan`` while preserving zeros.

    Args:
        sparse_matrix (sparse.spmatrix): The sparse matrix to densify, e.g. in csr format.

    Returns:
        The densified matrix.
    """
    dense = np.full(sparse_matrix.shape, np.nan)
    coo = sparse_matrix.tocoo()
    dense[coo.row, coo.col] = coo.data
    return dense


def sparsify_matrix(dense_matrix: np.ndarray) -> sp.csr_matrix:
    """Convert a dense matrix to a sparse matrix where ``np.nan`` are not explicitly stored.

    Args:
        dense_matrix (np.ndarray): Matrix to sparsify.

    Returns:
        The sparse matrix storing zeros explicitly and not storing ``np.nan``.
    """
    mask = ~np.isnan(dense_matrix)
    rows, cols = np.nonzero(mask)
    values = dense_matrix[mask]
    sparse_matrix = sp.csr_matrix((values, (rows, cols)), shape=dense_matrix.shape)
    return sparse_matrix


def global_reset_index(df: dd.DataFrame) -> dd.DataFrame:
    """Resets the index of a dask ``DataFrame`` globally instead of per partition.

    Args:
        df (dd.DataFrame ): Dask ``DataFrame`` to reset the index of.

    Returns:
        Dask ``DataFrame`` with a globally reset index.
    """
    index_name = "__tmp_idx"
    df = df.assign(**{index_name: 1})
    df = df.set_index((df[index_name].cumsum() - 1).rename(None))
    df = df.drop(columns=index_name)
    return df


def sanitize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize the dtypes of a ``DataFrame`` for compatibility with anndata.

    Args:
        df (pd.DataFrame): The ``DataFrame`` to sanitize.

    Returns:
        The ``DataFrame`` with sanitized dtypes.
    """
    for name, dtype in df.dtypes.items():
        if dtype == "string":
            df[name] = df[name].astype(object)
    return df
