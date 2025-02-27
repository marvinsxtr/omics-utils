from hydra_zen import builds

from omics_utils.configs.cluster import ClusterConfig
from omics_utils.configs.splitter_methyl import MethylationStratifiedSplitterConfig
from omics_utils.preprocessing.pipeline import PreprocessingPipeline
from omics_utils.preprocessing.steps.preprocessing import Preprocessing
from omics_utils.preprocessing.steps.stratifier import Stratifier

MethylationPreprocessingConfig = builds(
    PreprocessingPipeline,
    steps=[
        builds(
            Preprocessing,
            input_dir="/home/space/methyl_group/datasets/leitheiser_classification/pp_anndata/brain",
            n_debug=1,
            metadata_columns=["organ"],
            zen_partial=True,
        ),
        builds(
            Stratifier,
            splitter=MethylationStratifiedSplitterConfig,
            metadata_columns=["organ"],
            zen_partial=True,
        ),
    ],
    cluster=ClusterConfig,
    output_dir=None,
)
