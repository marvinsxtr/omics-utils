from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds

from omics_utils.utils.helpers import get_output_dir

ClusterConfig = builds(
    SLURMCluster,
    n_workers=4,
    queue="cpu-5h",
    cores=32,
    processes=16,
    memory="1024GiB",
    walltime="05:00:00",
    python="apptainer run oras://ghcr.io/bifold-pathomics/omics-utils:v0.0.23-sif python",
    log_directory=builds(get_output_dir),
)

LocalClusterConfig = builds(LocalCluster, n_workers=1, threads_per_worker=4)
