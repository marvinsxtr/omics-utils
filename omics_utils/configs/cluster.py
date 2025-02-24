from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds
from ml_project_template.common.utils.config import get_hydra_output_dir

ClusterConfig = builds(
    SLURMCluster,
    n_workers=10,
    queue="cpu-5h",
    cores=32,
    processes=4,
    memory="256GiB",
    python="apptainer exec docker://ghcr.io/bifold-pathomics/omics-utils:latest python",
    log_directory=builds(get_hydra_output_dir),
)

LocalClusterConfig = builds(LocalCluster, n_workers=1)
