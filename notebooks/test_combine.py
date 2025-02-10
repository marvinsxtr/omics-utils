# %%
from pathlib import Path
import anndata as ad
from tqdm import tqdm
import scanpy as sc
import pandas as pd
import uuid
import numpy as np
# %%
test_path = Path("/tmp/test")
test_path.mkdir(exist_ok=True)
cellxgene_path = Path("/home/space/omics/datasets/cellxgene/h5ads")
files = list(cellxgene_path.glob("*.h5ad"))
dataset_ids = [file.stem for file in files]
files
# %%
gene_vocab = pd.read_csv("../data/gene_vocabulary.csv", header=None, index_col=None, names=["name"])["name"].values
gene_vocab
# %%
def preprocess_adata(adata: ad.AnnData) -> ad.AnnData | None:
    """Preprocess an `AnnData` file and extract metadata."""
    # Define X to be the raw counts
    if hasattr(adata, "raw") and hasattr(adata.raw, "X"):
        assert adata.var.shape[0] == adata.raw.var.shape[0]
        adata.X = adata.raw.X
    else:
        assert (adata.X.astype("int") != adata.X).nnz == 0

    # Filter out non-human tissue, non-primary and diseased data
    cell_filter = (
        (adata.obs["organism_ontology_term_id"] == "NCBITaxon:9606") &
        (adata.obs["is_primary_data"] == True) &
        (adata.obs["disease"] == "normal") & 
        (adata.obs["assay"].isin(["10x 3' v1", "10x 3' v2", "10x 3' v3", "10x 5' v1", "10x 5' v2", 
                                  "10x 3' transcription profiling", "10x 5' transcription profiling"]))
    )

    # Only use genes in vocabulary
    gene_filter = adata.var.index.isin(gene_vocab.tolist())

    # Filter cells and genes
    adata = adata[cell_filter, gene_filter].copy()

    # Check if all cells/genes were filtered out
    if adata.n_obs == 0 or adata.n_vars == 0:
        return None

    # Preprocessing
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    return adata
# %%
metadata_path = test_path / "metadata"
metadata_path.mkdir(exist_ok=True)
data_path = test_path / "data"
data_path.mkdir(exist_ok=True)
# %%
def anndata_to_df(adata: ad.AnnData) -> tuple[pd.DataFrame, pd.DataFrame]:
    stratification_keys = ["sex", "tissue", "disease", "assay"]
    grouping_keys = ["donor_id"]

    obs = adata.obs

    # Assign case and sample identifiers
    obs["sample_id"] = [str(uuid.uuid4()) for _ in range(len(adata.obs))]
    obs["case_id"] = obs["donor_id"].map({id: str(uuid.uuid4()) for id in obs["donor_id"].unique()})
    obs = obs.set_index("sample_id")

    adata.obs = obs
    metadata = obs[["case_id"] + grouping_keys + stratification_keys].drop_duplicates().reset_index(drop=True)
    
    X = adata.X.toarray()
    X[X == 0] = np.nan

    df = pd.DataFrame(X, index=adata.obs_names, columns=adata.var_names)
    df = df.reindex(columns=gene_vocab, fill_value=np.nan)

    df["case_id"] = obs["case_id"]

    return metadata, df

def adata_to_parquet(h5ad_files: list[Path]) -> list[str]:
    """Preprocess adatas and convert to zarr."""
    for file in tqdm(h5ad_files):
        adata = ad.read_h5ad(file)
        adata = preprocess_adata(adata)

        if adata is None:
            continue

        metadata_df, data_df = anndata_to_df(adata)
        data_file_path = data_path / f"{file.stem}.parquet"
        metadata_file_path = metadata_path / f"{file.stem}.parquet"

        try:
            data_df.to_parquet(data_file_path)
            metadata_df.to_parquet(metadata_file_path)
        except KeyboardInterrupt:
            print("Cleaning up...")
            if data_file_path.exists():
                data_file_path.unlink()
            if metadata_file_path.exists():
                metadata_file_path.unlink()
            exit(0)

adata_to_parquet(files)
# %%

import dask.dataframe as dd

metadata_df = dd.read_parquet(metadata_path / "*.parquet").compute()
metadata_df = metadata_df.set_index("case_id")
metadata_df

# %%
data_df = dd.read_parquet(data_path / "*.parquet")
data_df.head(compute=False)
# %%
from sklearn.model_selection import StratifiedGroupKFold

stratification_keys = ["sex", "tissue"]
grouping_keys = ["donor_id"]

aggregated_strata = metadata_df[stratification_keys].astype(str).agg("_".join, axis=1)
aggregated_grouping = metadata_df[grouping_keys].astype(str).agg("_".join, axis=1)

num_folds = 2
sgf = StratifiedGroupKFold(n_splits=num_folds, shuffle=True, random_state=42)
# %%
metadata_df["fold"] = -1
fold_column_idx = metadata_df.columns.get_loc("fold")

for fold_idx, (_, test_idx) in enumerate(sgf.split(X=aggregated_strata, y=aggregated_strata, groups=aggregated_grouping)):
    metadata_df.iloc[test_idx, fold_column_idx] = fold_idx

metadata_df
# %%
joined_df = data_df.join(metadata_df, on="case_id", how="left")
joined_df.head(compute=False)
# %%
output_dir = test_path / "output"
output_dir.mkdir(exist_ok=True)

for fold_idx in range(num_folds):
    name_function = lambda x: f"fold_{fold_idx}_part_{x}.parquet"
    joined_df[joined_df["fold"] == fold_idx].sample(frac=1).to_parquet(output_dir, name_function=name_function)
# %%
