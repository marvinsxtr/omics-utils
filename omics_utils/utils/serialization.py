import base64
import io

import numpy as np
import scipy.sparse as sp


def serialize_sparse_matrix(sparse_matrix: sp.csr_matrix) -> str:
    """Serialize a sparse matrix row to bytes.

    Args:
        sparse_matrix: A scipy sparse matrix, typically a single row

    Returns:
        Serialized representation.
    """
    buffer = io.BytesIO()

    np.lib.format.write_array(buffer, np.array(sparse_matrix.shape))
    np.lib.format.write_array(buffer, sparse_matrix.data)
    np.lib.format.write_array(buffer, sparse_matrix.indices)
    np.lib.format.write_array(buffer, sparse_matrix.indptr)

    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def deserialize_sparse_matrix(serialized_str: str) -> sp.csr_matrix:
    """Deserialize string back to a sparse matrix row.

    Args:
        serialized_str: String representation of a sparse matrix

    Returns:
        Reconstructed sparse matrix.
    """
    buffer = io.BytesIO(base64.b64decode(serialized_str))

    shape = np.lib.format.read_array(buffer)
    data_array = np.lib.format.read_array(buffer)
    indices_array = np.lib.format.read_array(buffer)
    indptr_array = np.lib.format.read_array(buffer)

    return sp.csr_matrix((data_array, indices_array, indptr_array), shape=tuple(shape))
