from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds

from omics_utils.utils.helpers import get_output_dir

ClusterConfig = builds(
    SLURMCluster,
    n_workers=10,
    queue="cpu-2h",
    cores=16,
    processes=4,
    memory="128GiB",
    worker_extra_args=["--nthreads", "1"],
    python="apptainer exec oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif python",
    log_directory=builds(get_output_dir),
)

LocalClusterConfig = builds(LocalCluster, n_workers=1)

