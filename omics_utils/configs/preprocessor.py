from hydra_zen import builds
from steps.splitter import Splitter

from omics_utils.configs.cluster import (
    CellXGenePreprocessingClusterConfig,
    CellXGeneStratificationClusterConfig,
    HLCAPreprocessingClusterConfig,
    LocalClusterConfig,
)
from omics_utils.configs.converter import CellXGeneConverterConfig
from omics_utils.pipeline.pipeline import Pipeline
from omics_utils.steps.cellxgene.preprocessing import CellXGenePreprocessing
from omics_utils.steps.limiter import Limiter

CellXGenePreprocessingConfig = builds(
    Pipeline,
    steps=[
        builds(
            CellXGenePreprocessing,
            input_dir="/srv/data",
            converter=CellXGeneConverterConfig,
            n_debug=None,
            n_outer_partitions=50,
            n_inner_partitions=10,
            cluster=CellXGenePreprocessingClusterConfig,
            scale=6,
            zen_partial=True,
        ),
        builds(
            Splitter,
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

HLCAPreprocessingConfig = builds(
    Pipeline,
    steps=[
        builds(
            CellXGenePreprocessing,
            input_dir="/srv/data",
            converter=CellXGeneConverterConfig,
            n_debug=None,
            n_outer_partitions=5,
            n_inner_partitions=1,
            cluster=HLCAPreprocessingClusterConfig,
            scale=1,
            subset=["f72958f5-7f42-4ebb-98da-445b0c6de516"],
            only_primary=False,
            zen_partial=True,
        ),
        builds(
            Splitter,
            converter=CellXGeneConverterConfig,
            seed=42,
            n_partitions=5,
            cluster=HLCAPreprocessingClusterConfig,
            scale=1,
            zen_partial=True,
        ),
        builds(Limiter, cluster=LocalClusterConfig, zen_partial=True),
    ],
    cluster=None,
    output_dir=None,
)
