from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds

from omics_utils.utils.helpers import get_output_dir

ClusterConfig = builds(
    SLURMCluster,
    n_workers=20,
    queue="cpu-2h",
    cores=16,
    processes=9,
    memory="1024GiB",
    python="apptainer run oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif python",
    log_directory=builds(get_output_dir),
)

LocalClusterConfig = builds(LocalCluster, n_workers=1)
