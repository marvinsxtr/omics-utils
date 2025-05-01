import anndata as ad
import dask.array as da
import dask.dataframe as dd
import numpy as np
import pandas as pd
import scipy.sparse as sp

from omics_utils.transforms.anndata_converter import AnnDataConverter
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.serialization import deserialize_sparse_matrix


def test_anndata_to_dataframe_dask() -> None:
    """Test conversion from `AnnData` to dask DataFrame using sparse arrays."""
    X_dense = np.array([[1.0, 0.0, 3.0], [0.0, 2.0, 0.0]])
    X_dask = da.from_array(X_dense, chunks=(1, 3))
    X = X_dask.map_blocks(sp.csr_matrix)

    obs = pd.DataFrame(
        {
            ColumnNames.CASE_ID: ["case1", "case2"],
            ColumnNames.BATCH_ID: ["batch1", "batch2"],
            ColumnNames.SAMPLE_ID: ["sample1", "sample2"],
            "cell_type": ["A", "B"],
        }
    )
    var = pd.DataFrame(index=["gene1", "gene2", "gene3"])
    adata = ad.AnnData(X=X, obs=obs, var=var)

    converter = AnnDataConverter(obs_cols=["cell_type"], var_cols=["gene1", "gene2", "gene3"])

    delayed_objects = converter.anndata_to_dataframe(adata)
    ddf = dd.from_delayed(delayed_objects)
    df = ddf.compute()

    assert ColumnNames.SPARSE_VECTOR in df.columns
    assert "cell_type" in df.columns
    assert len(df) == 2

    vectors = []
    for i in range(len(df)):
        vec = deserialize_sparse_matrix(df[ColumnNames.SPARSE_VECTOR].iloc[i])
        vectors.append(vec)

    combined = sp.vstack(vectors)

    assert combined[0, 0] == 1.0
    assert combined[0, 2] == 3.0
    assert combined[1, 1] == 2.0


def test_dataframe_to_anndata_dask() -> None:
    """Test conversion from dask DataFrame to `AnnData` using sparse arrays."""
    X_dense = np.array([[1.0, 0.0, 3.0], [0.0, 2.0, 0.0]])
    X_dask = da.from_array(X_dense, chunks=(1, 3))
    X_original = X_dask.map_blocks(sp.csr_matrix)

    obs_original = pd.DataFrame(
        {
            ColumnNames.CASE_ID: ["case1", "case2"],
            ColumnNames.BATCH_ID: ["batch1", "batch2"],
            ColumnNames.SAMPLE_ID: ["sample1", "sample2"],
            "cell_type": ["A", "B"],
        }
    )
    var_original = pd.DataFrame(index=["gene1", "gene2", "gene3"])
    adata_original = ad.AnnData(X=X_original, obs=obs_original, var=var_original)

    converter = AnnDataConverter(obs_cols=["cell_type"], var_cols=["gene1", "gene2", "gene3"])

    delayed_objects = converter.anndata_to_dataframe(adata_original)
    ddf = dd.from_delayed(delayed_objects)
    df_original = ddf.compute()

    df = pd.DataFrame(
        {
            ColumnNames.SPARSE_VECTOR: df_original[ColumnNames.SPARSE_VECTOR],
            ColumnNames.SAMPLE_ID: ["sample1", "sample2"],
            ColumnNames.CASE_ID: ["case1", "case2"],
            ColumnNames.BATCH_ID: ["batch1", "batch2"],
            "cell_type": ["A", "B"],
        }
    )

    adata = converter.dataframe_to_anndata(df)

    assert adata.shape == (2, 3)
    assert list(adata.var_names) == ["gene1", "gene2", "gene3"]
    assert "cell_type" in adata.obs.columns
    assert ColumnNames.CASE_ID in adata.obs.columns

    assert adata.X[0, 0] == 1.0
    assert adata.X[0, 2] == 3.0
    assert adata.X[1, 1] == 2.0


def test_reindex_anndata_genes() -> None:
    """Test reindexing of genes with insertion of new genes using sparse arrays."""
    X_dense = np.array([[1.0, 0.0, 3.0], [0.0, 2.0, 0.0]])
    X_dask = da.from_array(X_dense, chunks=(1, 3))
    X = X_dask.map_blocks(sp.csr_matrix)

    obs = pd.DataFrame(
        {
            ColumnNames.CASE_ID: ["case1", "case2"],
            ColumnNames.SAMPLE_ID: ["sample1", "sample2"],
        }
    )
    var = pd.DataFrame(index=["gene1", "gene2", "gene3"])
    adata = ad.AnnData(X=X, obs=obs, var=var)

    converter = AnnDataConverter(obs_cols=[], var_cols=["gene1", "gene3", "gene4"])

    adata_reindexed = converter.reindex_anndata_genes(adata, ["gene1", "gene3", "gene4"])

    assert list(adata_reindexed.var_names) == ["gene1", "gene3", "gene4"]
    assert adata_reindexed.shape == (2, 3)

    X_reindexed_computed = adata_reindexed.X.compute()

    assert X_reindexed_computed[0, 0] == 1.0
    assert X_reindexed_computed[0, 1] == 3.0
    assert X_reindexed_computed[1, 1] == 0.0
    assert X_reindexed_computed[0, 2] == 0.0
    assert X_reindexed_computed[1, 2] == 0.0
