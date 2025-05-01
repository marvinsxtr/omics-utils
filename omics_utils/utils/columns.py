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
    GENE_ID: Final[str] = "gene_id"
    DISPERSIONS_NORM: Final[str] = "dispersions_norm"
