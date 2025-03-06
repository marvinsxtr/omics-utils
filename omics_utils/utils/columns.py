from dataclasses import dataclass
from typing import Final


@dataclass
class ColumnNames:
    """Common column names in `DataFrame`s."""

    FOLD: Final[str] = "fold"
    CASE_ID: Final[str] = "case_id"
    SAMPLE_ID: Final[str] = "sample_id"
    SPARSE_VECTOR: Final[str] = "sparse_vector"
