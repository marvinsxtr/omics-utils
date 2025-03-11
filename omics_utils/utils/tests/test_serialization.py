import numpy as np
import scipy.sparse as sp

from omics_utils.utils.serialization import deserialize_sparse_matrix, serialize_sparse_matrix


def test_csr_matrix_serialization() -> None:
    """Test serialization and deserialization of a sparse matrix to/from string."""
    data = np.array([1.5, 2.0, 3.5, 4.0])
    indices = np.array([0, 3, 1, 2])
    indptr = np.array([0, 2, 2, 4])
    shape = (3, 4)

    csr_matrix = sp.csr_matrix((data, indices, indptr), shape=shape)

    serialized = serialize_sparse_matrix(csr_matrix)

    assert isinstance(serialized, str), "Serialized output should be a string"

    deserialized = deserialize_sparse_matrix(serialized)

    assert sp.isspmatrix_csr(deserialized), "Deserialized object should be CSR matrix"

    assert deserialized.shape == csr_matrix.shape, "Shape mismatch"

    np.testing.assert_array_equal(deserialized.toarray(), csr_matrix.toarray(), err_msg="Matrix contents don't match")
<<<<<<< HEAD
=======
  
>>>>>>> c227e19 (Rebase on main)
