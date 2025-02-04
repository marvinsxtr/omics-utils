# %%
%load_ext memory_profiler
from pathlib import Path
import anndata as ad
import zarr
from tqdm import tqdm
import dask.array as da
import scanpy as sc
import pandas as pd
import traceback
# %%
cellxgene_path = Path("/home/space/omics/datasets/cellxgene/h5ads")
files = list(cellxgene_path.glob("*.h5ad"))
dataset_ids = [file.stem for file in files]
files
# %%
test_path = Path("/tmp/test")
test_path.mkdir(exist_ok=True)
# %%
def preprocess_adata(adata: ad.AnnData) -> ad.AnnData | None:
    """Preprocess an `AnnData` file and extract metadata."""
    # Filter out non-human tissue
    if not all(adata.obs["organism_ontology_term_id"] == "NCBITaxon:9606"):
        print("No human tissue found.")
        return None

    del adata.obsm
    del adata.obsp
    del adata.varm
    del adata.varp

    obs_keys = ["assay_ontology_term_id", "cell_type_ontology_term_id", "development_stage_ontology_term_id",
                "disease_ontology_term_id", "donor_id", "is_primary_data", "organism_ontology_term_id",
                "self_reported_ethnicity_ontology_term_id", "sex_ontology_term_id", "suspension_type", "tissue_type",
                "tissue_ontology_term_id", "assay", "cell_type", "development_stage", "disease", "observation_joinid",
                "organism", "self_reported_ethnicity", "sex", "tissue"]

    adata.obs = adata.obs[obs_keys]

    if hasattr(adata, "raw") and hasattr(adata.raw, "X"):
        # Make sure the processed genes were not filtered
        assert adata.var.shape[0] == adata.raw.var.shape[0]
        raw_x = adata.raw.X
    else:
        raw_x = adata.X

    new_adata = ad.AnnData(
        X=raw_x,
        obs=adata.obs,
        var=adata.var,
    )

    return new_adata


def preprocess_zarr(adata: ad.AnnData) -> ad.AnnData:

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    return adata

#%%

def read_dask(store):
    f = zarr.open(store, mode="r")

    def callback(func, elem_name: str, elem, iospec):
        if iospec.encoding_type in (
            "dataframe",
            "csr_matrix",
            "csc_matrix",
            "awkward-array",
        ):
            # Preventing recursing inside of these types
            return ad.io.read_elem(elem)
        elif iospec.encoding_type == "array":
            return da.from_zarr(elem)
        else:
            return func(elem)

    adata = ad.experimental.read_dispatched(f, callback=callback)

    return adata

def adata_to_zarr(h5ad_files: list[str]) -> list[str]:
    """Preprocess adatas and convert to zarr."""
    for i, f in enumerate(tqdm(h5ad_files)):
        file_path = test_path / f"file_{i}.zarr"

        if not file_path.exists():
            try:
                adata = ad.read_h5ad(f, backed="r+")
                adata = preprocess_adata(adata)

                if adata is None:
                    continue

                adata.write_zarr(file_path, chunks=True)
                zarr.consolidate_metadata(file_path)

                zarr_data = read_dask(file_path)

                preprocess_zarr(zarr_data)
            except Exception:
                print(traceback.format_exc())
                continue

        if i > 10:
            break

adata_to_zarr(files)

# %%
merged_path = test_path / "merged.zarr"
zarr_paths = list(test_path.glob("*.zarr"))
ad.experimental.concat_on_disk(zarr_paths, merged_path, join="outer")

# %%
full_data = zarr.open(merged_path, mode="r")
X = ad.experimental.read_elem_as_dask(full_data["X"])
X
# %%
zarr_data = read_dask(merged_path)
zarr_data
# %%
zarr_data.obs
# %%
stratification_keys = ["sex", "tissue", "disease", "assay"]
grouping_keys = ["donor_id"]
metadata = zarr_data.obs[grouping_keys + stratification_keys].drop_duplicates().reset_index(drop=True)
metadata
# %%
