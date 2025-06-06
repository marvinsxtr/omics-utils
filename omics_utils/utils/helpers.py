from pathlib import Path

import anndata as ad
import h5py
import pandas as pd
from ml_project_template.utils import get_hydra_output_dir


def get_output_dir() -> Path:
    """Get the current output directory.

    Returns:
        Output path of the current run.
    """
    try:
        output_dir = get_hydra_output_dir()
    except ValueError:
        output_dir = Path("/tmp/outputs")
        output_dir.mkdir(exist_ok=True, parents=True)
    return output_dir


def sanitize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize the dtypes of a `DataFrame` for compatibility with anndata.

    Args:
        df: The `DataFrame` to sanitize.

    Returns:
        The `DataFrame` with sanitized dtypes.
    """
    dtypes = {}
    for name, dtype in df.dtypes.items():
        if dtype == "string":
            dtypes[name] = object

    return df.astype(dtypes)


def read_anndata_dask(file_path: str, chunk_size: int = 100_000) -> ad.AnnData | None:
    """Read an `AnnData` file and store the sparse expression counts with dask.

    Args:
        file_path: Path to the .h5ad file to read.
        chunk_size: Chunk size to use for dask.

    Returns:
    An `AnnData` object containing dask-backed sparse expression counts in `X` or None if the encoding is not csr.
    """
    with h5py.File(file_path, "r") as f:
        adata = ad.AnnData(
            obs=ad.io.read_elem(f["obs"]),
            var=ad.io.read_elem(f["var"]),
        )

        source = f["raw/X"] if "raw/X" in f else f["X"]

        if source.attrs.get("encoding-type") != "csr_matrix":
            return None

        adata.X = ad.experimental.read_elem_as_dask(source, chunks=(chunk_size, adata.shape[1]))
    return adata


def read_genes(file_path: str) -> list[str]:
    """Read the gene names saved as a single-column csv file.

    Args:
        file_path: Path to read the genes from.

    Returns:
    A list of gene identifiers.
    """
    return pd.read_csv(file_path, header=None, index_col=None, names=["name"])["name"].to_numpy().tolist()
