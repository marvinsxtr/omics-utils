from tempfile import TemporaryDirectory

from hydra_zen import instantiate, launch
from omegaconf import DictConfig

from omics_utils.configs.cluster import LocalClusterConfig
from omics_utils.configs.preprocessor import CellXGenePreprocessingConfig, MethylationPreprocessingConfig


def wrap(config: DictConfig) -> None:
    """Instantiates a given config."""
    instantiate(config)


def test_preprocessing_configs() -> None:
    """Test config instantiation of preprocessing pipelines."""
    configs = [
        CellXGenePreprocessingConfig(cluster=LocalClusterConfig),
        MethylationPreprocessingConfig(cluster=LocalClusterConfig),
    ]

    with TemporaryDirectory() as tmp_dir:
        input_override = f"steps.0.input_dir={tmp_dir}"

        for config in configs:
            launch(
                config,
                task_function=wrap,
                overrides=[input_override],
            )
