from hydra_zen import builds

from omics_utils.configs.cluster import (
    CellXGenePartitioningClusterConfig,
    CellXGeneSplittingClusterConfig,
    HLCAClusterConfig,
    LocalClusterConfig,
)
from omics_utils.configs.transforms import CellXGeneConverterConfig, CellXGeneFiltererConfig, HLCAFiltererConfig
from omics_utils.pipeline.pipeline import Pipeline
from omics_utils.steps.limiter import Limiter
from omics_utils.steps.partitioner import Partitioner
from omics_utils.steps.selector import Selector
from omics_utils.steps.splitter import Splitter

CellXGenePipelineConfig = builds(
    Pipeline,
    steps=[
        builds(
            Selector,
            input_dir="/srv/data",
            filterer=CellXGeneFiltererConfig,
            var_cols=["feature_name", "feature_length"],
            n_highly_variable=5000,
            cluster=CellXGenePartitioningClusterConfig,
            scale=6,
            zen_partial=True,
        ),
        builds(
            Partitioner,
            input_dir="/srv/data",
            converter=CellXGeneConverterConfig,
            filterer=CellXGeneFiltererConfig,
            n_debug=None,
            n_outer_partitions=50,
            n_inner_partitions=10,
            cluster=CellXGenePartitioningClusterConfig,
            scale=6,
            zen_partial=True,
        ),
        builds(
            Splitter,
            converter=CellXGeneConverterConfig,
            seed=42,
            n_partitions=1000,
            cluster=CellXGeneSplittingClusterConfig,
            scale=6,
            zen_partial=True,
        ),
        builds(Limiter, cluster=LocalClusterConfig, zen_partial=True),
    ],
    cluster=None,
    output_dir=None,
)

HLCAPipelineConfig = builds(
    Pipeline,
    steps=[
        builds(
            Selector,
            input_dir="/srv/data",
            filterer=HLCAFiltererConfig,
            var_cols=["feature_name", "feature_length"],
            gene_file="/home/space/omics/datasets/depmap/depmap_hvgs.csv",
            cluster=HLCAClusterConfig,
            subset=["f72958f5-7f42-4ebb-98da-445b0c6de516"],
            scale=1,
            zen_partial=True,
        ),
        builds(
            Partitioner,
            input_dir="/srv/data",
            converter=CellXGeneConverterConfig,
            filterer=HLCAFiltererConfig,
            n_debug=None,
            n_outer_partitions=5,
            n_inner_partitions=1,
            cluster=HLCAClusterConfig,
            subset=["f72958f5-7f42-4ebb-98da-445b0c6de516"],
            scale=1,
            zen_partial=True,
        ),
        builds(
            Splitter,
            converter=CellXGeneConverterConfig,
            seed=42,
            n_partitions=5,
            cluster=HLCAClusterConfig,
            scale=1,
            zen_partial=True,
        ),
        builds(Limiter, cluster=LocalClusterConfig, zen_partial=True),
    ],
    cluster=None,
    output_dir=None,
)
