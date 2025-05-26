from hydra_zen import builds

from omics_utils.transforms.anndata_converter import AnnDataConverter
from omics_utils.transforms.anndata_filterer import CellXGeneFilterer

OBS_COLS = [
    "sex",
    "tissue",
    "disease",
    "assay",
    "cell_type",
    "organism",
    "tissue_type",
    "development_stage",
    "suspension_type",
    "self_reported_ethnicity",
    "assay_ontology_term_id",
    "cell_type_ontology_term_id",
    "development_stage_ontology_term_id",
    "disease_ontology_term_id",
    "organism_ontology_term_id",
    "self_reported_ethnicity_ontology_term_id",
    "sex_ontology_term_id",
    "tissue_ontology_term_id",
]

ORGANISMS = ["Homo sapiens"]

ASSAYS = [
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

TISSUES = [
    "ovary",
    "blood",
    "colon",
    "bladder organ",
    "lung",
    "kidney",
    "breast",
    "brain",
    "skin of body",
    "stomach",
    "lymph node",
    "bone marrow",
    "prostate gland",
    "skin of face",
    "ampulla of uterine tube",
    "lamina propria",
    "liver",
    "esophagus",
    "endometrium",
    "small intestine",
    "adrenal gland",
    "decidua",
    "spleen",
    "eye",
    "vein",
    "muscle tissue",
    "endocrine pancreas",
]

DISEASES = [
    "adenocarcinoma",
    "premalignant hematological system disease",
    "non-small cell lung carcinoma",
    "lung large cell carcinoma",
    "clear cell renal carcinoma",
    "breast cancer",
    "B-cell acute lymphoblastic leukemia",
    "glioblastoma",
    "normal",
    "gastric cancer",
    "blastoma",
    "B-cell non-Hodgkin lymphoma",
    "squamous cell lung carcinoma",
    "small cell lung carcinoma",
    "tongue cancer",
    "lung adenocarcinoma",
    "Wilms tumor",
    "follicular lymphoma",
    "neuroendocrine carcinoma",
]

CellXGeneConverterConfig = builds(
    AnnDataConverter,
    obs_cols=OBS_COLS,
    zen_partial=True,
)

HLCAFilterConfig = builds(dict, organism=ORGANISMS, assay=ASSAYS, is_primary_data=[False])
CellXGeneFilterConfig = builds(dict, organism=ORGANISMS, assay=ASSAYS, is_primary_data=[True])
CellXGeneSubsetFilterConfig = builds(
    dict,
    organism=ORGANISMS,
    assay=ASSAYS,
    is_primary_data=[True],
    tissue=TISSUES,
    disease=DISEASES,
)

CellXGeneFiltererConfig = builds(CellXGeneFilterer, genes=None, obs_filters=CellXGeneFilterConfig, zen_partial=True)
CellXGeneSubsetFiltererConfig = builds(
    CellXGeneFilterer, genes=None, obs_filters=CellXGeneSubsetFilterConfig, zen_partial=True
)
HLCAFiltererConfig = builds(
    CellXGeneFilterer,
    genes=None,
    obs_filters=HLCAFilterConfig,
    zen_partial=True,
)
