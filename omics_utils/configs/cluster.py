from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds

from omics_utils.utils.helpers import get_output_dir

ClusterConfig = builds(
    SLURMCluster,
    n_workers=10,
    queue="cpu-2h",
    cores=32,
    processes=17,
    memory="2048GiB",
    python="apptainer run oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif python",
    log_directory=builds(get_output_dir),
)

LocalClusterConfig = builds(LocalCluster, n_workers=1)
