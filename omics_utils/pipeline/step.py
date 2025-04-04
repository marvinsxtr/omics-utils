from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from dask.distributed import Client, LocalCluster
from dask_jobqueue import JobQueueCluster
from hydra_zen.typing import Partial
from ml_project_template.utils import logger


class Step(ABC):
    """Base preprocessing step in a modular ETL pipeline. Also see `PreprocessingPipeline`."""

    def __init__(
        self,
        base_dir: str,
        cluster: Partial[JobQueueCluster | LocalCluster] | None = None,
        scale: int | None = None,
    ) -> None:
        """Initializes an instance of a base preprocessing step.

        Args:
            base_dir: Folder where a subfolder is created for each preprocessing step.
            cluster: Configured cluster to use for distributed preprocessing using `dask`.
            scale: Number of workers to use in the cluster. Only relevant when `cluster` is given.
        """
        base_path = Path(base_dir)

        input_path = base_path / self.input_step if self.input_step is not None else None
        output_path = base_path / self.output_step

        self.base_path = base_path
        self.input_path = input_path
        self.output_path = output_path
        self.cluster = cluster
        self.scale = scale

    @property
    @abstractmethod
    def input_step(self) -> str | None:
        """Name of the preprocessing step preceding this one or `None` if this is the first."""
        ...

    @property
    @abstractmethod
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        ...

    @abstractmethod
    def read(self, *args: Any) -> Any:
        """Read the data from the previous step or the input data.

        Args:
            args: The input data, e.g. file paths.

        Returns:
            str: The data ready for transformation.
        """
        ...

    @abstractmethod
    def transform(self, *args: Any) -> Any:
        """Transform the data.

        Args:
            args: The input data.

        Returns:
            The transformed output.
        """
        ...

    @abstractmethod
    def write(self, *args: Any) -> None:
        """Save the result of the transformation.

        Args:
            args: The transformed data.
        """
        ...

    @contextmanager
    def cluster_context(self) -> Generator[Client, None, None]:
        """Context manager for cluster lifecycle management.

        Yields:
            A dask Client connected to the configured cluster.
        """
        client = None
        try:
            if self.cluster is not None:
                cluster: JobQueueCluster | LocalCluster = self.cluster()
                if isinstance(cluster, LocalCluster):
                    logger.info("Running locally...")
                else:
                    logger.info(f"Running the following job script:\n{cluster.job_script()}")
                    cluster.scale(jobs=self.scale)

                client = Client(cluster)
                logger.info(f"View dask dashboard at {client.dashboard_link}")

            yield client

        finally:
            if client is not None:
                client.shutdown()

    def run_step(self) -> None:
        """Run the pipeline step."""
        with self.cluster_context() as _client:
            self.run()

    @abstractmethod
    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running `read`, `transform` and `write`."""
        ...
