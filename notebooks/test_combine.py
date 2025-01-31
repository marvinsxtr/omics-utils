# %%
#%load_ext memory_profiler
from pathlib import Path

import anndata as ad
import zarr
from tqdm import tqdm
import scipy.sparse as sp
import numpy as np
# %%
cellxgene_path = Path("/home/space/omics/datasets/cellxgene/h5ads")
files = list(cellxgene_path.glob("*.h5ad"))
dataset_ids = [file.stem for file in files]

files
# %%
test_path = Path("/tmp/test")
test_path.mkdir(exist_ok=True)
# %%
def normalize_csr(X_csr: sp.csr_array, target_sum: int = 1e4, log: bool = True) -> sp.csr_array:
    """Normalize the single cell data and optionally take the log1p."""
    cell_sums = np.array(X_csr.sum(axis=1)).flatten()
    scaling_factors = sp.diags(target_sum / cell_sums)
    X_norm = scaling_factors.dot(X_csr)

    if log:
        X_norm.data = np.log1p(X_norm.data)

    X_norm.sort_indices()
    return X_norm

def preprocess_adata(adata: ad.AnnData) -> ad.AnnData:

    stratification_keys = ["sex", "tissue", "disease"]
    grouping_keys = ["donor_id"]

    obs_keys = ["assay_ontology_term_id", "cell_type_ontology_term_id", "development_stage_ontology_term_id",
                "disease_ontology_term_id", "donor_id", "is_primary_data", "organism_ontology_term_id",
                "self_reported_ethnicity_ontology_term_id", "sex_ontology_term_id", "suspension_type", "tissue_type",
                "tissue_ontology_term_id", "assay", "cell_type", "development_stage", "disease", "observation_joinid",
                "organism", "self_reported_ethnicity", "sex", "tissue"]

    print(adata.obs["assay"].drop_duplicates())

    adata.obs = adata.obs[obs_keys]

    raw_x = adata.raw.X if hasattr(adata, "raw") and hasattr(adata.raw, "X") else adata.X
    norm_x = normalize_csr(raw_x.to_memory())

    print("norm", norm_x[0])
    print("raw", raw_x[0])
    print("X", adata.X[0])

    adata = adata[adata.obs["organism_ontology_term_id"] == "NCBITaxon:9606", :] # Human tissue
    return adata


#%%

def adata_to_zarr(h5ad_files) -> list[str]:
    zarr_paths = []

    for i, f in enumerate(tqdm(h5ad_files)):
        file_path = test_path / f"file_{i}.zarr"

        if not file_path.exists():
            adata = ad.read_h5ad(f, backed="r")
            adata = preprocess_adata(adata)

            # TODO(marvin): Clean the data and select (un)-normalized X.  # noqa: TD003

            adata.write_zarr(file_path)
            zarr.consolidate_metadata(file_path)

        zarr_paths.append(file_path)

        #break
        if i > 9:
            break

zarr_paths = adata_to_zarr(files)

# %%
merged_path = test_path / "merged.zarr"
ad.experimental.concat_on_disk(zarr_paths, merged_path, join="outer")

# %%
full_data = zarr.open(merged_path, mode="r")
X = ad.experimental.read_elem_as_dask(full_data["X"])
X
# %%
