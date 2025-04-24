from hydra_zen import builds, store
from ml_project_template.runs import Run

from omics_utils.configs.pipeline import (
    CellXGenePipelineConfig,
    HLCAPipelineConfig,
)
from omics_utils.preprocess import main

RunConfig = builds(Run, seed=42, wandb=None, job=None)
MainConfig = builds(main, cfg=RunConfig, populate_full_signature=True)

store(
    MainConfig,
    name="root",
    hydra_defaults=[
        "_self_",
        {"cfg/wandb": None},
        {"pipeline": "cellxgene"},
    ],
)

pipeline_store = store(group="pipeline")
pipeline_store(CellXGenePipelineConfig, name="cellxgene")
pipeline_store(HLCAPipelineConfig, name="hlca")
