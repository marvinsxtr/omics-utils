from hydra_zen import builds

from omics_utils.converter.anndata_converter import AnndataConverter

CellXGeneConverterConfig = builds(
    AnndataConverter,
    obs_cols=[
        "sex",
        "tissue",
        "disease",
        "assay",
        "cell_type",
        "organism",
        "assay_ontology_term_id",
        "cell_type_ontology_term_id",
        "development_stage_ontology_term_id",
        "disease_ontology_term_id",
        "organism_ontology_term_id",
        "self_reported_ethnicity_ontology_term_id",
        "sex_ontology_term_id",
        "suspension_type",
        "tissue_type",
        "tissue_ontology_term_id",
        "development_stage",
        "self_reported_ethnicity",
    ],
    var_cols_file="/home/space/omics/datasets/vocabulary/gene_vocabulary.csv",
)

MethylationConverterConfig = builds(
    AnndataConverter,
    obs_cols=["organ", "category"],
    sparse=False,
)
