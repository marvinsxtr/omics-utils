import numpy as np
from scipy import sparse

from omics_utils.utils.helpers import densify_matrix, sparsify_matrix


def test_densify_matrix() -> None:
    """Test sparse to dense conversion with a small matrix."""
    sparse_mat = sparse.csr_matrix(([1.0, 0.0, 3.0], ([0, 0, 1], [0, 1, 2])), shape=(2, 3))

    result = densify_matrix(sparse_mat)
    expected = np.array([[1.0, 0.0, np.nan], [np.nan, np.nan, 3.0]])

    mask = ~np.isnan(expected)
    assert np.array_equal(result[mask], expected[mask])
    assert np.array_equal(np.isnan(result), np.isnan(expected))


def test_sparsify_matrix() -> None:
    """Test dense to sparse conversion with a small matrix."""
    dense_mat = np.array([[1.0, 0.0, np.nan], [np.nan, np.nan, 3.0]])

    result = sparsify_matrix(dense_mat)
    expected = sparse.csr_matrix(([1.0, 0.0, 3.0], ([0, 0, 1], [0, 1, 2])), shape=(2, 3))

    assert (result != expected).nnz == 0
    assert result.nnz == expected.nnz
    assert np.array_equal(result.indptr, expected.indptr)
    assert np.array_equal(result.indices, expected.indices)
    assert np.array_equal(result.data, expected.data)
