from dataclasses import dataclass, field
from typing import Final


@dataclass
class ColumnNames:
    """Common column names in `DataFrame`s."""

    FOLD: Final[str] = "fold"
    CASE_ID: Final[str] = "case_id"
    SAMPLE_ID: Final[str] = "sample_id"


@dataclass
class PossibleColumnNames:
    """Possible different spellings of ColumnNames."""

    SAMPLE_ID: Final[list[str]] = field(
        default_factory=lambda: [
            "sample_ID",
            "Sample_ID",
            "sampleId",
            "sampleid",
            "SampleID",
            "specimen_id",
            "Specimen_ID",
            "specimenId",
            "specimenid",
            "SpecimenID",
        ]
    )

    CASE_ID: Final[list[str]] = field(
        default_factory=lambda: [
            "case_ID",
            "Case_ID",
            "caseId",
            "caseid",
            "CaseID",
            "donor_id",
            "Donor_ID",
            "donorId",
            "donorid",
            "DonorID",
            "patient_id",
            "Patient_ID",
            "patientId",
            "patientid",
            "PatientID",
        ]
    )
