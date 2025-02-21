from hydra_zen import builds

from omics_utils.configs.cluster import ClusterConfig
from omics_utils.configs.splitter import CellXGeneStratifiedSplitterConfig
from omics_utils.preprocessing.pipeline import PreprocessingPipeline
from omics_utils.preprocessing.steps.cellxgene import CellXGenePreprocessing
from omics_utils.preprocessing.steps.stratifier import Stratifier

CellXGenePreprocessingConfig = builds(
    PreprocessingPipeline,
    steps=[
        builds(
            CellXGenePreprocessing,
            input_dir="/home/space/omics/datasets/cellxgene/h5ads",
            gene_vocab_path="/home/space/omics/datasets/vocabulary/gene_vocabulary.csv",
            zen_partial=True,
        ),
        builds(
            Stratifier,
            splitter=CellXGeneStratifiedSplitterConfig,
            metadata_columns=["sex", "tissue", "disease", "assay"],
            zen_partial=True,
        ),
    ],
    cluster=ClusterConfig,
    output_dir="/home/marvinsxtr/Projects/omics-utils/outputs/2025-02-21/10-06-08",
)
