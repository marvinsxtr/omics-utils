import anndata
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy import sparse

from omics_utils.utils.helpers import densify_matrix, reindex_anndata_genes, sparsify_matrix


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


def test_reindex_anndata_genes() -> None:
    """Reindex AnnData object to match a specified gene list while preserving sparsity."""
    data = np.array([1.0, 2.0, 3.0, 4.0])
    indices = np.array([0, 1, 2, 0])
    indptr = np.array([0, 2, 3, 4])
    X = sp.csr_matrix((data, indices, indptr), shape=(3, 4))

    var = pd.DataFrame(index=["gene_A", "gene_B", "gene_C", "gene_D"])
    var["type"] = ["type1", "type2", "type1", "type2"]

    obs = pd.DataFrame(index=["cell_1", "cell_2", "cell_3"])
    obs["batch"] = ["batch1", "batch2", "batch1"]

    adata = anndata.AnnData(X=X, var=var, obs=obs)

    expected_original = np.array(
        [
            [1.0, 2.0, 0.0, 0.0],
            [0.0, 0.0, 3.0, 0.0],
            [4.0, 0.0, 0.0, 0.0],
        ]
    )
    np.testing.assert_array_equal(adata.X.toarray(), expected_original)

    # Test case 1: Reorder and subset genes
    new_genes = ["gene_C", "gene_A", "gene_E"]
    result = reindex_anndata_genes(adata, new_genes)

    assert result.shape == (3, 3)
    assert list(result.var_names) == new_genes

    expected_reindexed = np.array(
        [
            [0.0, 1.0, 0.0],
            [3.0, 0.0, 0.0],
            [0.0, 4.0, 0.0],
        ]
    )
    np.testing.assert_array_equal(result.X.toarray(), expected_reindexed)

    # Test case 2: No overlap between gene lists
    no_overlap_genes = ["gene_F", "gene_G"]
    empty_result = reindex_anndata_genes(adata, no_overlap_genes)

    assert empty_result.shape == (3, 2)
    expected_empty = np.zeros((3, 2))
    np.testing.assert_array_equal(empty_result.X.toarray(), expected_empty)
