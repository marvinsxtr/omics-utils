from hydra_zen import builds

from omics_utils.converter.anndata_converter import AnndataConverter

CellXGeneConverterConfig = builds(
    AnndataConverter,
    obs_cols=["sex", "tissue", "disease", "assay"],
    var_cols_file="/home/space/omics/datasets/vocabulary/gene_vocabulary.csv",
)

MethylationConverterConfig = builds(
    AnndataConverter,
    obs_cols=["organ", "category"],
)
