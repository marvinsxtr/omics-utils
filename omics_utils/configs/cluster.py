from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds
from ml_project_template.common.utils.config import get_hydra_output_dir

ClusterConfig = builds(
    SLURMCluster,
    n_workers=10,
    queue="cpu-2h",
    cores=8,
    processes=1,
    memory="128GiB",
    python="apptainer exec oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif python",
    log_directory=builds(get_hydra_output_dir),
)

LocalClusterConfig = builds(LocalCluster, n_workers=1)
