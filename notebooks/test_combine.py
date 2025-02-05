# %%
from pathlib import Path
import anndata as ad
from tqdm import tqdm
import scanpy as sc
import pandas as pd
# %%
test_path = Path("/tmp/test")
test_path.mkdir(exist_ok=True)
cellxgene_path = Path("/home/space/omics/datasets/cellxgene/h5ads")
files = list(cellxgene_path.glob("*.h5ad"))
dataset_ids = [file.stem for file in files]
files
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

    adata = ad.AnnData(
        X=raw_x.to_memory(),
        obs=adata.obs,
        var=adata.var,
    )

    scales_counts = sc.pp.normalize_total(adata, target_sum=1e4, inplace=False)
    adata.X = sc.pp.log1p(scales_counts["X"])

    return adata
# %%
import uuid
import numpy as np

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
    df["case_id"] = obs["case_id"]

    return metadata, df

def adata_to_zarr(h5ad_files: list[Path]) -> list[str]:
    """Preprocess adatas and convert to zarr."""
    metadata_path = test_path / "metadata"
    metadata_path.mkdir(exist_ok=True)
    data_path = test_path / "data"
    data_path.mkdir(exist_ok=True)

    for file in tqdm(h5ad_files):
        adata = ad.read_h5ad(file, backed="r")
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
            data_file_path.unlink()
            metadata_file_path.unlink()
            exit(0)

adata_to_zarr(files[10:])
# %%
from sklearn.model_selection import StratifiedGroupKFold

stratification_keys = ["sex", "tissue", "disease", "assay"]
grouping_keys = ["donor_id"]

aggregated_strata = metadata[stratification_keys].astype(str).agg("_".join, axis=1)
aggregated_grouping = metadata[grouping_keys].astype(str).agg("_".join, axis=1)

sgf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
# %%
print(aggregated_strata, aggregated_grouping)

metadata["fold"] = -1
fold_column_idx = metadata.columns.get_loc("fold")

for fold_idx, (_, test_idx) in enumerate(sgf.split(X=aggregated_strata, y=aggregated_strata, groups=aggregated_grouping)):
    metadata.iloc[test_idx, fold_column_idx] = fold_idx