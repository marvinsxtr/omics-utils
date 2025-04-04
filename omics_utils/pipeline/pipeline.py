from pathlib import Path

from dask.distributed import LocalCluster
from dask_jobqueue import JobQueueCluster
from hydra_zen.typing import Partial
from ml_project_template.utils import logger

from omics_utils.pipeline.step import Step
from omics_utils.utils.helpers import get_output_dir


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
        scale: int | None = None,
    ) -> None:
        """Initializes an instance of a preprocessing pipeline.

        Args:
            steps: Preprocessing steps to perform in sequence
            output_dir: Output path to save intermediate and final preprocessing outputs in. By default,
                this is the hydra output directory ("outputs").
            force_recompute: Whether to recompute already existing intermediate results.
            cluster: Configured cluster to use for distributed preprocessing using `dask`. This config will be used
                for all steps in the pipeline.
            scale: Number of jobs to start on the cluster.
        """
        if isinstance(cluster, JobQueueCluster) and scale is None:
            raise ValueError("Please provide a `scale` parameter in addition to the cluster config.")

        output_path = get_output_dir() if output_dir is None else Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if cluster is None:
            steps: list[Step] = [step(base_dir=output_path) for step in steps]
        else:
            steps: list[Step] = [step(base_dir=output_path, cluster=cluster, scale=scale) for step in steps]

        self.steps = steps
        self.output_path = output_path
        self.force_recompute = force_recompute
        self.cluster = cluster
        self.scale = scale

    def run(self) -> None:
        """Run the preprocessing pipeline on the data."""
        for step in self.steps:
            if step.output_path.exists() and not self.force_recompute:
                logger.info(f"Skipping step {step.output_step}...")
                continue

            step.output_path.mkdir(exist_ok=True)
            step.run_step()
