# %%
from cellarium.ml.data import IterableDistributedAnnDataCollectionDataset as AnnDataLoader
from cellarium.ml.data import DistributedAnnDataCollection
from cellarium.ml.utilities.data import AnnDataField

import yaml

with open("/home/marvinsxtr/Projects/omics-utils/outputs/2025-03-07/17-06-05/stratification/limits.yaml", "r") as f:
    limits = yaml.safe_load(f)

fold_idx = 0
fold_limits = limits[fold_idx]
fold_limits[-1] = fold_limits[-1] + 1 # TODO: Fix this

paths = f"/home/marvinsxtr/Projects/omics-utils/outputs/2025-03-07/17-06-05/stratification/split/fold_{fold_idx}_part_{{0..5}}.h5ad"

dadc = DistributedAnnDataCollection(
    paths,
    limits=fold_limits,
    max_cache_size=4
)

dl = AnnDataLoader(
    dadc,
    batch_keys={
        "X": AnnDataField(attr="X"),
        "var_names": AnnDataField(attr="var_names"),
    },
    batch_size=1000,
    iteration_strategy="cache_efficient",
    shuffle=True,
    seed=42,
    drop_last=False
)

for batch in dl:
    print(batch)

# %%
