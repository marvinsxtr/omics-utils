from hydra_zen import builds, store
from ml_project_template.runs import Run
from ml_project_template.wandb import WandBConfig

from omics_utils.configs.preprocessor import (
    CellXGenePreprocessingConfig,
    HLCAPreprocessingConfig,
    MethylationPreprocessingConfig,
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
        {"preprocessor": "cellxgene"},
    ],
)

wandb_store = store(group="cfg/wandb")
wandb_store(WandBConfig, name="base")

preproc_store = store(group="preprocessor")
preproc_store(CellXGenePreprocessingConfig, name="cellxgene")
preproc_store(MethylationPreprocessingConfig, name="methylation")
preproc_store(HLCAPreprocessingConfig, name="hlca")
