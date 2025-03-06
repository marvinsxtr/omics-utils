from hydra_zen import builds, store
from ml_project_template.configs.logging.wandb import WandBConfig
from ml_project_template.configs.runs.base import JobConfig, RunConfig

from omics_utils.configs.preprocessor import CellXGenePreprocessingConfig, MethylationPreprocessingConfig
from omics_utils.preprocess import main

main_config = builds(main, cfg=RunConfig, populate_full_signature=True)
store(
    main_config,
    name="root",
    hydra_defaults=["_self_", {"cfg/wandb": None}, {"cfg/job": None}, {"preprocessor": "cellxgene"}],
)

wandb_store = store(group="cfg/wandb")
wandb_store(WandBConfig, name="base")

job_store = store(group="cfg/job")
job_store(JobConfig, name="base")

preproc_store = store(group="preprocessor")
preproc_store(CellXGenePreprocessingConfig, name="cellxgene")
preproc_store(MethylationPreprocessingConfig, name="methylation")
