from dataclasses import dataclass
from typing import Final


@dataclass
class ColumnNames:
    """Common column names in a `DataFrame`."""

    FOLD: Final[str] = "fold"
    CASE_ID: Final[str] = "case_id"
    SAMPLE_ID: Final[str] = "sample_id"
    BATCH_ID: Final[str] = "batch_id"
    SPARSE_VECTOR: Final[str] = "sparse_vector"
    HIGHLY_VARIABLE: Final[str] = "highly_variable"
    COLUMN_ID: Final[str] = "column_id"
