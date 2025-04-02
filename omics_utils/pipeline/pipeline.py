from pathlib import Path

from dask.distributed import Client, LocalCluster
from dask_jobqueue import JobQueueCluster
from hydra_zen.typing import Partial
from ml_project_template.common.logging.logger import logger

from omics_utils.pipeline.step import Step
from omics_utils.utils.helpers import get_output_dir
from omics_utils.pipeline.step import Step


# TODO(marvin): Write documentation of the input schema this class expects.
# https://github.com/bifold-pathomics/omics-utils/issues/1
class Pipeline:
    """Handles a sequence of preprocessing steps in an ETL style pipeline.

    Can be used for the preprocessing, concatenation, stratification, splitting and saving of tabular omics datasets.
    """

    def __init__(
        self,
        steps: list[Partial[Step]],
        output_dir: str | None = None,
        force_recompute: bool = False,
        cluster: JobQueueCluster | LocalCluster | None = None,
        scale: int = 10,
    ) -> None:
        """Initializes an instance of a preprocessing pipeline.

        Args:
            steps: Preprocessing steps to perform in sequence
            output_dir: Output path to save intermediate and final preprocessing outputs in. By default,
                this is the hydra output directory ("outputs").
            force_recompute: Whether to recompute already existing intermediate results.
            cluster: Configured cluster to use for distributed preprocessing
                using `dask`
            scale: Number of jobs to start on the cluster. Defaults to 10.
        """
        output_path = get_output_dir() if output_dir is None else Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.steps = [step(base_dir=output_path) for step in steps]
        self.output_path = output_path
        self.force_recompute = force_recompute
        self.cluster = cluster
        self.scale = scale

    def _setup_cluster(self, cluster: JobQueueCluster | LocalCluster) -> None:
        """Configures the Slurm cluster for multi-node processing using dask.

        Args:
            cluster: The dask jobqueue cluster to use.
        """
        if isinstance(cluster, LocalCluster):
            logger.info("Running locally...")
        else:
            logger.info(
                f"Running the following job script:\n{cluster.job_script()}")

        client = Client(cluster)

        logger.info(f"View dask dashboard at {client.dashboard_link}")

    def run(self) -> None:
        """Run the preprocessing pipeline on the data."""
        if self.cluster is not None:
            if not isinstance(self.cluster, LocalCluster):
                self.cluster.scale(jobs=self.scale)
            self._setup_cluster(self.cluster)

        for step in self.steps:
            if step.output_path.exists() and not self.force_recompute:
                logger.info(f"Skipping step {step.output_step}...")
                continue

            step.output_path.mkdir(exist_ok=True)
            step.run()
