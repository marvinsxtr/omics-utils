from pathlib import Path

from dask.distributed import Client
from dask_jobqueue import JobQueueCluster
from hydra_zen.typing import Partial
from ml_project_template.common.logging.logger import logger
from ml_project_template.common.utils.config import get_hydra_output_dir

from omics_utils.preprocessing.steps.step import PreprocessingStep


# TODO(marvin): Write documentation of the input schema this class expects.
# https://github.com/bifold-pathomics/omics-utils/issues/1
class PreprocessingPipeline:
    """Handles a sequence of preprocessing steps in an ETL style pipeline.

    Can be used for the preprocessing, concatenation, stratification, splitting and saving of tabular omics datasets.
    """

    def __init__(
        self,
        steps: list[Partial[PreprocessingStep]],
        output_dir: str | None = None,
        force_recompute: bool = False,
        cluster: JobQueueCluster | None = None,
    ) -> None:
        """Args:
        ----
          steps: Preprocessing steps to perform in sequence.
          output_dir: Output path to save intermediate and final preprocessing outputs in. By default this is the
            hydra output directory (`outputs`).
          force_recompute: Whether to recompute already existing intermediate results.
          cluster: Configured cluster to use for distributed preprocessing using dask.
        """
        output_path = get_hydra_output_dir() if output_dir is None else Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.steps = [step(base_dir=output_path) for step in steps]
        self.output_path = output_path
        self.force_recompute = force_recompute

        if cluster is not None:
            self._setup_cluster(cluster)

    def _setup_cluster(self, cluster: JobQueueCluster) -> None:
        """Configures the Slurm cluster for multi-node processing using dask.

        Args:
        ----
          cluster: The dask jobqueue cluster to use.
        """
        logger.info(f"Running the following job script:\n{cluster.job_script()}")
        client = Client(cluster)
        logger.info(f"View dask dashboard at {client.dashboard_link}")

    def run(self) -> None:
        """Run the preprocessing pipeline on the data."""
        for step in self.steps:
            if step.output_path.exists() and not self.force_recompute:
                logger.info(f"Skipping step {step.output_step}...")
                continue

            step.output_path.mkdir(exist_ok=True)
            step.run()
