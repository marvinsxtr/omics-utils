# %%
from cellarium.ml.data import IterableDistributedAnnDataCollectionDataset as AnnDataLoader
from cellarium.ml.data import DistributedAnnDataCollection
from cellarium.ml.utilities.data import AnnDataField, densify


dadc = DistributedAnnDataCollection(
    "/temp/test/fold_0_part_{0..5}.h5ad",
    limits=[500, 1000, 2000, 2500, 3000, 4000],
    max_cache_size=2)

dl = AnnDataLoader(
    dadc,
    batch_keys={
        "X": AnnDataField(attr="X", convert_fn=densify),
        "var_names": AnnDataField(attr="var_names"),
    },
    batch_size=5000,
    iteration_strategy="cache_efficient",
    shuffle=True,
    shuffle_seed=42,
    drop_last_indices=True
)

for batch in dl:
    print(batch)
    break