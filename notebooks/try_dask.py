# %%
import dask.array as da
import dask.dataframe as dd
import h5py 
import anndata as ad
import pandas as pd
import base64
import io

import numpy as np
import scipy.sparse as sp
import dask
from dask.distributed import print

def serialize_sparse_matrix(sparse_matrix: sp.csr_matrix) -> str:
    """Serialize a sparse matrix row to bytes.

    Args:
    ----
      sparse_matrix: A scipy sparse matrix (typically a single row)

    Returns:
    -------
    Serialized representation
    """
    buffer = io.BytesIO()

    np.lib.format.write_array(buffer, np.array(sparse_matrix.shape))
    np.lib.format.write_array(buffer, sparse_matrix.data)
    np.lib.format.write_array(buffer, sparse_matrix.indices)
    np.lib.format.write_array(buffer, sparse_matrix.indptr)

    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("ascii")

input_files = [
    "/home/space/omics/datasets/cellxgene/h5ads/1f1c5c14-5949-4c81-b28e-b272e271b672.h5ad"
]

def process_partition(block, obs_names_part):
    """Process a partition of data.
    
    Args:
        block: A block of the dask array
        obs_names_part: Observation names for this partition
        
    Returns:
        DataFrame with serialized sparse vectors
    """
    print(block)
    sparse_vectors = []
    for i in range(block.shape[0]):
        row_sparse = sp.csr_matrix(block[i])
        sparse_vectors.append(serialize_sparse_matrix(row_sparse))
    
    return pd.DataFrame({"sparse_vector": sparse_vectors}, index=obs_names_part)

def transform(file_path):
    with h5py.File(file_path, "r") as f:
        adata = ad.AnnData(
            obs=ad.io.read_elem(f["obs"]),
            var=ad.io.read_elem(f["var"]),
        )
        X_dask = ad.experimental.read_elem_as_dask(
            f["raw/X"] if "raw/X" in f else f["X"], chunks=(25000, adata.shape[1])
        )
        obs_names = adata.obs_names.copy()

    print(adata)

    dask_tasks = []
    
    # Get the partitioning information from the dask array
    offsets = np.cumsum((0,) + X_dask.chunks[0])
    
    # Create a delayed task for each partition
    for i in range(len(X_dask.chunks[0])):
        # Get the chunk of data and matching obs_names
        start, end = offsets[i], offsets[i+1]
        chunk = X_dask[start:end]
        obs_chunk = obs_names[start:end]
        
        # Create a delayed task that will compute and process this chunk
        print(chunk)
        task = dask.delayed(lambda x, names: process_partition(x, names))(chunk, obs_chunk)
        dask_tasks.append(task)
    
    # Create a dataframe from these delayed tasks
    meta = pd.DataFrame({"sparse_vector": [""]})
    meta.index.name = adata.obs_names.name
    
    return dd.from_delayed(dask_tasks, meta=meta)
data_df = dd.from_map(transform, input_files, meta=pd.DataFrame({"sparse_vector": [""]}))
# %%
data_df.compute().compute()
# %%
