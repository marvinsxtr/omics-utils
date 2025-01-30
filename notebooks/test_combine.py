# %%
%load_ext memory_profiler
from pathlib import Path

import anndata as ad
import zarr
from tqdm import tqdm

# %%
cellxgene_path = Path("/home/space/omics/datasets/cellxgene/h5ads")
files = list(cellxgene_path.glob("*.h5ad"))
dataset_ids = [file.stem for file in files]

files
# %%
test_path = Path("/tmp/test")
test_path.mkdir(exist_ok=True)
# %%
zarr_paths = []

for i, f in enumerate(tqdm(files)):
    file_path = test_path / f"file_{i}.zarr"

    if not file_path.exists():
        adata = ad.read_h5ad(f, backed="r")

        # TODO(marvin): Clean the data and select (un)-normalized X.  # noqa: TD003

        adata.write_zarr(file_path)
        zarr.consolidate_metadata(file_path)

    zarr_paths.append(file_path)

    if i > 9:
        break

# %%
merged_path = test_path / "merged.zarr"
ad.experimental.concat_on_disk(zarr_paths, merged_path, join="outer")

# %%
full_data = zarr.open(merged_path, mode="r")
X = ad.experimental.read_elem_as_dask(full_data["X"])
X
# %%
