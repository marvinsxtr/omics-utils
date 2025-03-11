from unittest.mock import patch

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.serialization import deserialize_sparse_matrix


def test_anndata_to_dataframe_sparse() -> None:
    """Test conversion from AnnData to DataFrame using sparse format."""
    X = sp.csr_matrix(np.array([[1.0, 0.0, 3.0], [0.0, 2.0, 0.0]]))
    obs = pd.DataFrame({ColumnNames.CASE_ID: ["case1", "case2"], "cell_type": ["A", "B"]})
    var = pd.DataFrame(index=["gene1", "gene2", "gene3"])
    adata = ad.AnnData(X=X, obs=obs, var=var)

    converter = AnndataConverter(sparse=True, obs_cols=["cell_type"], var_cols=["gene1", "gene2", "gene3"])

    with patch("uuid.uuid4", side_effect=["sample1", "sample2", "case1_new", "case2_new"]):
        df = converter.anndata_to_dataframe(adata)

    assert ColumnNames.SPARSE_VECTOR in df.columns
    assert "cell_type" in df.columns
    assert len(df) == 2

    row1_vector = deserialize_sparse_matrix(df[ColumnNames.SPARSE_VECTOR].iloc[0])
    assert row1_vector[0, 0] == 1.0

    row2_vector = deserialize_sparse_matrix(df[ColumnNames.SPARSE_VECTOR].iloc[1])
    assert row2_vector[0, 0] == 0.0


def test_dataframe_to_anndata_sparse() -> None:
    """Test conversion from DataFrame to AnnData using sparse format."""
    X_original = sp.csr_matrix(np.array([[1.0, 0.0, 3.0], [0.0, 2.0, 0.0]]))
    obs_original = pd.DataFrame({ColumnNames.CASE_ID: ["case1", "case2"], "cell_type": ["A", "B"]})
    var_original = pd.DataFrame(index=["gene1", "gene2", "gene3"])
    adata_original = ad.AnnData(X=X_original, obs=obs_original, var=var_original)

    converter = AnndataConverter(sparse=True, obs_cols=["cell_type"], var_cols=["gene1", "gene2", "gene3"])

    with patch("uuid.uuid4", side_effect=["sample1", "sample2", "case1_new", "case2_new"]):
        df_original = converter.anndata_to_dataframe(adata_original)

    df = pd.DataFrame(
        {
            ColumnNames.SPARSE_VECTOR: df_original[ColumnNames.SPARSE_VECTOR],
            ColumnNames.SAMPLE_ID: ["sample1", "sample2"],
            ColumnNames.CASE_ID: ["case1", "case2"],
            ColumnNames.FOLD: ["0", "1"],
            "cell_type": ["A", "B"],
        }
    )

    adata = converter.dataframe_to_anndata(df)

    assert adata.shape == (2, 3)
    assert list(adata.var_names) == ["gene1", "gene2", "gene3"]
    assert "cell_type" in adata.obs.columns
    assert ColumnNames.CASE_ID in adata.obs.columns
    assert ColumnNames.FOLD in adata.obs.columns

    assert adata.X[0, 0] == 1.0
    assert adata.X[0, 2] == 3.0
    assert adata.X[1, 1] == 2.0


def test_reindex_anndata_genes() -> None:
    """Test reindexing of genes with insertion of new genes."""
    X = sp.csr_matrix(np.array([[1.0, 0.0, 3.0], [0.0, 2.0, 0.0]]))
    obs = pd.DataFrame(
        {
            ColumnNames.CASE_ID: ["case1", "case2"],
            ColumnNames.SAMPLE_ID: ["sample1", "sample2"],
        }
    )
    var = pd.DataFrame(index=["gene1", "gene2", "gene3"])
    adata = ad.AnnData(X=X, obs=obs, var=var)

    converter = AnndataConverter(obs_cols=[], var_cols=["gene1", "gene3", "gene4"])

    adata_reindexed = converter.reindex_anndata_genes(adata, ["gene1", "gene3", "gene4"])

    assert list(adata_reindexed.var_names) == ["gene1", "gene3", "gene4"]
    assert adata_reindexed.shape == (2, 3)

    assert adata_reindexed.X[0, 0] == 1.0
    assert adata_reindexed.X[0, 1] == 3.0
    assert adata_reindexed.X[1, 1] == 0.0
    assert adata_reindexed.X[0, 2] == 0.0
    assert adata_reindexed.X[1, 2] == 0.0
  
