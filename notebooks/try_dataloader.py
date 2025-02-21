# %%
# Hack to make it work with newer versions.
# from anndata.compat import Index, Index1D
# import anndata
# anndata._core.index.Index = Index
# anndata._core.index.Index1D = Index1D

from cellarium.ml.data import IterableDistributedAnnDataCollectionDataset as AnnDataLoader
from cellarium.ml.data import DistributedAnnDataCollection
from cellarium.ml.utilities.data import AnnDataField, densify

import yaml

with open("/home/marvinsxtr/Projects/omics-utils/outputs/2025-02-21/10-06-08/stratification/limits.yaml", "r") as f:
    limits = yaml.safe_load(f)

fold_idx = 0
fold_limits = limits[fold_idx]

print(fold_limits)

paths = f"/home/marvinsxtr/Projects/omics-utils/outputs/2025-02-21/10-06-08/stratification/split/fold_{fold_idx}_part_{{0..5}}.h5ad"

dadc = DistributedAnnDataCollection(
    paths,
    limits=fold_limits,
    max_cache_size=2
)

dl = AnnDataLoader(
    dadc,
    batch_keys={
        "X": AnnDataField(attr="X"),
        "var_names": AnnDataField(attr="var_names"),
    },
    batch_size=5000,
    iteration_strategy="cache_efficient",
    shuffle=True,
    seed=42,
    drop_last=True
)

for batch in dl:
    print(batch)

# %%
