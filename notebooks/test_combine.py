# %%
#%load_ext memory_profiler
from pathlib import Path
from typing import Union

import anndata as ad
import zarr
from tqdm import tqdm
import scipy.sparse as sp
import dask.array as da
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
def preprocess_adata(adata: ad.AnnData) -> ad.AnnData:
    # TODO(marvin): Clean the data and select (un)-normalized X.  # noqa: TD003

    del adata.obsm
    del adata.obsp
    del adata.varm
    del adata.varp

    stratification_keys = ["sex", "tissue", "disease"]
    grouping_keys = ["donor_id"]

    obs_keys = ["assay_ontology_term_id", "cell_type_ontology_term_id", "development_stage_ontology_term_id",
                "disease_ontology_term_id", "donor_id", "is_primary_data", "organism_ontology_term_id",
                "self_reported_ethnicity_ontology_term_id", "sex_ontology_term_id", "suspension_type", "tissue_type",
                "tissue_ontology_term_id", "assay", "cell_type", "development_stage", "disease", "observation_joinid",
                "organism", "self_reported_ethnicity", "sex", "tissue"]

    print(adata.obs["assay"].drop_duplicates())

    adata.obs = adata.obs[obs_keys]

    adata.X = adata.raw.X if hasattr(adata, "raw") and hasattr(adata.raw, "X") else adata.X
    del adata.raw

    adata = adata[adata.obs["organism_ontology_term_id"] == "NCBITaxon:9606", :] # Human tissue
    return adata


def preprocess_zarr(zarr_data: zarr.Group):
    dask_X = ad.experimental.read_elem_as_dask(
        zarr_data.raw.X if hasattr(zarr_data, "raw") and hasattr(zarr_data.raw, "X") else zarr_data.X
    )

    row_sums = dask_X.map_blocks(
        lambda x: x.sum(axis=1).A1.reshape(-1, 1),
        chunks=(dask_X.chunks[0], (1,)),
        drop_axis=1,
        new_axis=1,
        dtype=dask_X.dtype
    )

    def normalize_and_log(x, sums):
        scale_factors = 1e4 / sums.flatten()
        scaled = sp.diags(scale_factors) @ x
        scaled.data = np.log1p(scaled.data)
        return scaled

    final_X = dask_X.map_blocks(
        normalize_and_log,
        row_sums,
        dtype=dask_X.dtype
    )

    final_X = final_X.compute()
    print(final_X)

#%%

def adata_to_zarr(h5ad_files) -> list[str]:
    zarr_paths = []

    for i, f in enumerate(tqdm(h5ad_files)):
        file_path = test_path / f"file_{i}.zarr"

        if not file_path.exists():
            adata = ad.read_h5ad(f, backed="r+")

            adata = preprocess_adata(adata)

            adata.write_zarr(file_path, chunks=True)
            zarr.consolidate_metadata(file_path)

            zarr_data = zarr.open(file_path)
            preprocess_zarr(zarr_data)

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
