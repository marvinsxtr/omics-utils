from pathlib import Path

from dask.distributed import LocalCluster
from hydra_zen import builds, instantiate, launch
from omegaconf import DictConfig

from omics_utils.configs.pipeline import CellXGenePipelineConfig


def wrap(config: DictConfig) -> None:
    """Instantiates a given config."""
    instantiate(config)


def test_preprocessing_configs(tmp_path: Path) -> None:
    """Test config instantiation of preprocessing pipelines."""
    DummyClusterConfig = builds(LocalCluster, n_workers=0, silence_logs=True, processes=False)

    input_override = f"steps.0.input_dir={tmp_path}"
    tmp_path.touch()

    configs = [
        (CellXGenePipelineConfig(cluster=DummyClusterConfig), [input_override]),
    ]

    for config, overrides in configs:
        launch(config, task_function=wrap, overrides=overrides)
