import itertools
import uuid
from pathlib import Path

import anndata as ad
import dask.bag as db
import dask.dataframe as dd
import h5py
from dask.delayed import Delayed

from omics_utils.converter.anndata_converter import AnndataConverter
from omics_utils.pipeline.steps.preprocessing import Preprocessing
from omics_utils.utils.columns import ColumnNames


class CellXGenePreprocessing(Preprocessing):
    """Preprocessing of CellXGene `AnnData` files."""

    def __init__(
        self,
        *args,
        input_dir: str,
        converter: AnndataConverter,
        n_debug: int | None = None,
        chunk_size: int = 100000,
        n_outer_partitions: int = 50,
        subset: list[str] | None = None,
        only_primary: bool = True,
        **kwargs,
    ) -> None:
        """
        Args:
            input_dir: Folder where the input CellXGene `AnnData` files are saved.
            converter: Converter to convert `AnnData` into a `DataFrame` format.
            n_debug: Take the first n input files only for debugging purposes.
            chunk_size: Chunk size of the expression matrix in dask.
            n_outer_partitions: Number of output partitions.
            subset: Subset of .h5ad file names to process.
            only_primary: Whether to only process cells marked as primary data.
        """  # noqa: D212
        super().__init__(*args, converter=converter, input_dir=input_dir, n_debug=n_debug, **kwargs)
        self.chunk_size = chunk_size
        self.n_outer_partitions = n_outer_partitions
        self.subset = subset
        self.only_primary = only_primary

    def read(self, input_files: list[Path]) -> dd.DataFrame:
        """Read and transform the data from the the input data.

        NOTE: In this case the read step contains the transform step for compatibility with dask.

        Args:
            input_files: File paths to process in parallel.

        Returns:
            The data ready for transformation.
        """
        if self.n_debug is not None:
            input_files = input_files[: self.n_debug]

        if self.subset is not None:
            input_files = [f for f in input_files if f.stem in self.subset]

        return (
            db.from_sequence(input_files)
            .map(self.transform)
            .flatten()
            .repartition(npartitions=self.n_outer_partitions)
        )

    def transform(self, file_path: Path) -> list[Delayed]:
        """Preprocess a single `AnnData` file.

        Args:
            file_path: Path to the `AnnData` file to be transformed.

        Returns:
            A list of `Delayed` tasks for preprocessing.
        """
        with h5py.File(file_path, "r") as f:
            adata = ad.AnnData(
                obs=ad.io.read_elem(f["obs"]),
                var=ad.io.read_elem(f["var"]),
            )

            source = f["raw/X"] if "raw/X" in f else f["X"]

            encoding = source.attrs.get("encoding-type")

            if encoding == "csr_matrix":
                adata.X = ad.experimental.read_elem_as_dask(source, chunks=(self.chunk_size, adata.shape[1]))
            elif encoding == "csc_matrix":
                return []
            else:
                raise NotImplementedError(f"The encoding {encoding} is not implemented.")

        adata.obs = adata.obs.rename(columns={"donor_id": ColumnNames.CASE_ID})
        adata.obs[ColumnNames.BATCH_ID] = str(file_path.stem)

        # Filter out non-human tissue, non-primary and diseased data
        cell_filter = (adata.obs["organism_ontology_term_id"] == "NCBITaxon:9606") & (
            adata.obs["assay"].isin(
                [
                    "10x transcription profiling",
                    "10x 3' transcription profiling",
                    "10x 3' v1",
                    "10x 3' v2",
                    "10x 3' v3",
                    "10x 3' v4",
                    "10x 5' transcription profiling",
                    "10x 5' v1",
                    "10x 5' v2",
                    "10x 5' v3",
                ]
            )
        )
        if self.only_primary:
            cell_filter = cell_filter & (adata.obs["is_primary_data"] == True)

        gene_filter = adata.var.index.isin(self.converter.var_cols)
        adata = adata[cell_filter, gene_filter].copy()

        return self.converter.anndata_to_dataframe(adata)

    def write(self, data_df: dd.DataFrame) -> None:
        """Load/save the result of the transformation.

        Args:
            data_df: A `DataFrame` containing the patient/donor metadata and the matrix `X`.
        """
        data_df.repartition(npartitions=self.n_inner_partitions, force=True).to_parquet(
            self.output_path, filesystem="arrow", name_function=lambda _: f"{uuid.uuid4()!s}.parquet"
        )

    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read` and `write`."""
        input_files = list(self.input_path.glob("*.h5ad"))
        delayed = self.read(input_files)

        def process(delayed_iterator: itertools.chain) -> None:
            """Process a partition of tasks."""
            delayed_list = list(delayed_iterator)

            if len(delayed_list) > 0:
                data_df = dd.from_delayed(delayed_list, meta=self.meta_df)
                self.write(data_df)

        delayed.map_partitions(process).compute()
