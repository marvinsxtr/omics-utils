from hydra_zen import builds
from sklearn.model_selection import StratifiedShuffleSplit

from omics_utils.splitting.splitter import StratifiedSplitter

StratifiedTrainTestSplitConfig = builds(
    StratifiedShuffleSplit,
    n_splits=1,
    test_size=0.2,
    random_state=42,
)

CellXGeneStratifiedSplitterConfig = builds(
    StratifiedSplitter,
    sklearn_splitter=StratifiedTrainTestSplitConfig,
    stratification_columns=["sex", "tissue", "disease", "assay"],
)
