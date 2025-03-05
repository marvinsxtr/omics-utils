import uuid
from pathlib import Path

import anndata as ad
import dask.dataframe as dd
import pandas as pd
import scanpy as sc

from omics_utils.preprocessing.steps.step import PreprocessingStep
from omics_utils.utils.columns import ColumnNames
from omics_utils.utils.helpers import reindex_anndata_genes, remove_empty_partitions
from omics_utils.utils.serialization import serialize_sparse_matrix


class CellXGenePreprocessing(PreprocessingStep):
    """Preprocessing of CellXGene `AnnData` files."""

    def __init__(self, *args, input_dir: str, gene_vocab_file: str, n_debug: int | None = None, **kwargs) -> None:
        """Args:
        ----
          input_dir: Folder where the input CellXGene `AnnData` files are saved.
          gene_vocab_file: Path to the gene vocabulary to filter by.
          n_debug: Take the first n input files only for debugging purposes.
        """
        super().__init__(*args, **kwargs)

        input_path = Path(input_dir)
        gene_vocab_path = Path(gene_vocab_file)

        if not input_path.exists():
            raise ValueError("Input path does not exist.")

        if not gene_vocab_path.exists():
            raise ValueError("Gene vocab path does not exist.")

        self.gene_vocab = (
            pd.read_csv(gene_vocab_path, header=None, index_col=None, names=["name"])["name"].to_numpy().tolist()
        )
        self.gene_vocab_path = gene_vocab_path
        self.input_path = input_path
        self.n_debug = n_debug

    @property
    def input_step(self) -> str | None:
        """Has no preceding preprocessing step."""
        return None

    @property
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        return "data"

    @property
    def metadata_columns(self) -> list[str]:
        """Return the columns in `AnnData.obs` that are considered metadata."""
        return ["sex", "tissue", "disease", "assay"]

    def read(self) -> dd.DataFrame:
        """Read and transform the data from the the input data.

        NOTE: In this case the read step contains the transform step for compatibility with dask.

        Returns
        -------
        The data ready for transformation.
        """
        input_files = list(self.input_path.glob("*.h5ad"))

        if self.n_debug is not None:
            input_files = input_files[: self.n_debug]

        data_df = dd.from_map(self.transform, input_files)
        data_df = remove_empty_partitions(data_df)
        return data_df

    def transform(self, file_path: Path) -> pd.DataFrame:
        """Preprocess a single `AnnData` file.

        Args:
        ----
          file_path: Path to the `AnnData` file to be transformed.

        Returns:
        -------
        The preprocessed data as a pandas `DataFrame`.
        """
        adata = ad.read_h5ad(file_path)

        # Define X to be the raw counts
        if hasattr(adata, "raw") and hasattr(adata.raw, "X"):
            if adata.var.shape[0] != adata.raw.var.shape[0]:
                raise ValueError("Number of raw variables has to match the number of preprocessed variables.")
            adata.X = adata.raw.X
        elif ((adata.X.astype("int") != adata.X).nnz != 0) and ((adata.X < 0).nnz == 0):
            raise ValueError("X has to contain raw expression counts.")

        # Filter out non-human tissue, non-primary and diseased data
        cell_filter = (
            (adata.obs["organism_ontology_term_id"] == "NCBITaxon:9606")
            & (adata.obs["is_primary_data"] == True)
            & (adata.obs["disease"] == "normal")
            & (
                adata.obs["assay"].isin(
                    [
                        "10x 3' v1",
                        "10x 3' v2",
                        "10x 3' v3",
                        "10x 5' v1",
                        "10x 5' v2",
                        "10x 3' transcription profiling",
                        "10x 5' transcription profiling",
                    ]
                )
            )
        )

        # Only use genes in vocabulary
        gene_filter = adata.var.index.isin(self.gene_vocab)

        # Filter cells and genes
        adata = adata[cell_filter, gene_filter].copy()

        # Check if all cells/genes were filtered out
        if adata.n_obs == 0 or adata.n_vars == 0:
            return self.anndata_to_df(adata)

        # Preprocessing
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)

        return self.anndata_to_df(adata)

    def anndata_to_df(self, adata: ad.AnnData) -> pd.DataFrame:
        """Convert a CellXGene `AnnData` file to a pandas `DataFrame` containing `X` and the metadata.

        Args:
        ----
          adata: The already preprocessed `AnnData` object to be converted.

        Returns:
        -------
        A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        obs = adata.obs

        # Assign case and sample identifiers
        obs[ColumnNames.SAMPLE_ID] = [str(uuid.uuid4()) for _ in range(len(adata.obs))]
        obs[ColumnNames.SAMPLE_ID] = obs[ColumnNames.SAMPLE_ID].astype(str)
        obs[ColumnNames.CASE_ID] = (
            obs["donor_id"].map({donor_id: str(uuid.uuid4()) for donor_id in obs["donor_id"].unique()}).astype(str)
        )
        obs = obs.set_index(ColumnNames.SAMPLE_ID, drop=False).rename_axis(None)

        adata.obs = obs

        adata = reindex_anndata_genes(adata, self.gene_vocab)
        serialized_cells = [serialize_sparse_matrix(x) for x in adata.X]

        df = pd.DataFrame({"cells": serialized_cells}, index=adata.obs_names).astype(str)
        df = df.join(obs[[ColumnNames.CASE_ID, ColumnNames.SAMPLE_ID, *self.metadata_columns]].astype(str))

        return df

    def write(self, data_df: dd.DataFrame) -> None:
        """Load/save the result of the transformation.

        Args:
        ----
          data_df: A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        data_df.to_parquet(self.output_path, filesystem="arrow", name_function=lambda part: f"part_{part}.parquet")

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read` and `write`."""
        data_df = self.read()
        self.write(data_df)
