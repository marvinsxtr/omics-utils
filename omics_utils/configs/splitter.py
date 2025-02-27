from hydra_zen import builds

from omics_utils.splitting.splitter import StratifiedSplitter

CellXGeneStratifiedSplitterConfig = builds(
    StratifiedSplitter,
    num_folds=2,
    shuffle=True,
    seed=42,
    stratification_columns=["sex", "tissue", "disease", "assay"],
)


MethylationStratifiedSplitterConfig = builds(
    StratifiedSplitter,
    num_folds=2,
    shuffle=True,
    seed=42,
    stratification_columns=["organ"],
)
