from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds

from omics_utils.utils.helpers import get_output_dir

CellXGenePreprocessingClusterConfig = builds(
    SLURMCluster,
    n_workers=2,
    queue="cpu-5h",
    cores=32,
    processes=16,
    memory="2048GiB",
    walltime="05:00:00",
    python="apptainer run oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif python",
    log_directory=builds(get_output_dir),
    zen_partial=True,
)

CellXGeneStratificationClusterConfig = CellXGenePreprocessingClusterConfig(processes=8)

LocalClusterConfig = builds(LocalCluster, n_workers=1, threads_per_worker=4)
