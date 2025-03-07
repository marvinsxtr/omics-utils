from pathlib import Path

from hydra_zen import instantiate, launch
from omegaconf import DictConfig

from omics_utils.configs.cluster import LocalClusterConfig
from omics_utils.configs.preprocessor import CellXGenePreprocessingConfig, MethylationPreprocessingConfig


def wrap(config: DictConfig) -> None:
    """Instantiates a given config."""
    instantiate(config)


def test_preprocessing_configs(tmp_path: Path) -> None:
    """Test config instantiation of preprocessing pipelines."""
    input_override = f"steps.0.input_dir={tmp_path}"

    var_cols_file = tmp_path / "genes.csv"
    var_cols_file.touch()
    var_cols_overrides = [f"steps.{index}.converter.var_cols_file={var_cols_file}" for index in range(2)]

    configs = [
        (CellXGenePreprocessingConfig(cluster=LocalClusterConfig), [input_override, *var_cols_overrides]),
        (MethylationPreprocessingConfig(cluster=LocalClusterConfig), [input_override]),
    ]

    for config, overrides in configs:
        launch(config, task_function=wrap, overrides=overrides)
