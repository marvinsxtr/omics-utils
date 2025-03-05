import base64
import io

import numpy as np
import scipy.sparse as sp


def serialize_sparse_row(row: sp.spmatrix) -> bytes:
    """Serialize a sparse matrix row to bytes.

    Args:
    ----
      row: A scipy sparse matrix (typically a single row)

    Returns:
    -------
    Serialized bytes representation
    """
    if not sp.isspmatrix_csr(row):
        row = row.tocsr()

    buffer = io.BytesIO()

    np.savez(buffer, data=row.data, indices=row.indices, indptr=row.indptr, shape=row.shape)

    buffer.seek(0)
    return base64.b64encode(buffer.getvalue())


def deserialize_sparse_row(serialized_str: str) -> sp.csr_matrix:
    """Deserialize bytes back to a sparse matrix row.

    Args:
    ----
      serialized_str: String representation of a sparse matrix

    Returns:
    -------
    Reconstructed sparse matrix
    """
    serialized_bytes = base64.b64decode(serialized_str)

    buffer = io.BytesIO(serialized_bytes)
    loaded = np.load(buffer)

    return sp.csr_matrix((loaded["data"], loaded["indices"], loaded["indptr"]), shape=tuple(loaded["shape"]))
