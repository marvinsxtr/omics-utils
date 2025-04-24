from pathlib import Path

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
