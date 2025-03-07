from ml_project_template.common.utils.config import run
from ml_project_template.configs.runs.base import Run

from omics_utils.pipeline.pipeline import Pipeline


def main(cfg: Run, preprocessor: Pipeline) -> None:  # noqa: ARG001
    """Run the preprocessing pipeline."""
    preprocessor.run()


if __name__ == "__main__":
    import omics_utils.configs.stores.preprocess  # noqa: F401

    run(main)
