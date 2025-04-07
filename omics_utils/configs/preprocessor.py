from hydra_zen import builds

from omics_utils.configs.cluster import (
    CellXGenePreprocessingClusterConfig,
    CellXGeneStratificationClusterConfig,
    LocalClusterConfig,
)
from omics_utils.configs.converter import CellXGeneConverterConfig, MethylationConverterConfig
from omics_utils.configs.splitter import MethylationStratifiedSplitterConfig
from omics_utils.pipeline.pipeline import Pipeline
from omics_utils.pipeline.steps.cellxgene import CellXGenePreprocessing
from omics_utils.pipeline.steps.limiter import Limiter
from omics_utils.pipeline.steps.methylation import MethylationPreprocessing
from omics_utils.pipeline.steps.splitting import Splitting
from omics_utils.pipeline.steps.stratifier import Stratifier

CellXGenePreprocessingConfig = builds(
    Pipeline,
    steps=[
        builds(
            CellXGenePreprocessing,
            input_dir="/home/space/omics/datasets/cellxgene/h5ads",
            converter=CellXGeneConverterConfig,
            n_debug=None,
            n_outer_partitions=50,
            n_inner_partitions=10,
            cluster=CellXGenePreprocessingClusterConfig,
            scale=6,
            zen_partial=True,
        ),
        builds(
            Splitting,
            converter=CellXGeneConverterConfig,
            seed=42,
            n_partitions=1000,
            cluster=CellXGeneStratificationClusterConfig,
            scale=6,
            zen_partial=True,
        ),
        builds(Limiter, cluster=LocalClusterConfig, zen_partial=True),
    ],
    cluster=None,
    output_dir=None,
)

MethylationPreprocessingConfig = builds(
    Pipeline,
    steps=[
        builds(
            MethylationPreprocessing,
            input_dir="/home/space/methyl_group/datasets/leitheiser_classification/pp_anndata/lung",
            converter=MethylationConverterConfig,
            n_debug=2,
            n_partitions=10,
            zen_partial=True,
        ),
        builds(
            Stratifier,
            splitter=MethylationStratifiedSplitterConfig,
            converter=MethylationConverterConfig,
            seed=42,
            zen_partial=True,
        ),
        builds(Limiter, zen_partial=True),
    ],
    cluster=LocalClusterConfig,
    output_dir=None,
)
