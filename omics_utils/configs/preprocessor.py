from hydra_zen import builds

from omics_utils.configs.cluster import ClusterConfig
from omics_utils.configs.splitter import CellXGeneStratifiedSplitterConfig, MethylationStratifiedSplitterConfig
from omics_utils.preprocessing.pipeline import PreprocessingPipeline
from omics_utils.preprocessing.steps.cellxgene import CellXGenePreprocessing
from omics_utils.preprocessing.steps.preprocessing import Preprocessing
from omics_utils.preprocessing.steps.stratifier import Stratifier

CellXGenePreprocessingConfig = builds(
    PreprocessingPipeline,
    steps=[
        builds(
            CellXGenePreprocessing,
            input_dir="/home/space/omics/datasets/cellxgene/h5ads",
            gene_vocab_file="/home/space/omics/datasets/vocabulary/gene_vocabulary.csv",
            n_debug=None,
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
    output_dir=None,
)


MethylationPreprocessingConfig = builds(
    PreprocessingPipeline,
    steps=[
        builds(
            Preprocessing,
            input_dir="/home/space/methyl_group/datasets/leitheiser_classification/pp_anndata/brain",
            n_debug=2,
            metadata_columns=["organ", "category"],
            zen_partial=True,
        ),
        builds(
            Stratifier,
            splitter=MethylationStratifiedSplitterConfig,
            metadata_columns=["organ", "category"],
            zen_partial=True,
        ),
    ],
    cluster=ClusterConfig,
    output_dir=None,
)
