from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds

from omics_utils.utils.helpers import get_output_dir

CellXGenePreprocessingClusterConfig = builds(
    SLURMCluster,
    n_workers=4,
    queue="cpu-2h",
    cores=16,
    processes=8,
    memory="512GiB",
    walltime="02:00:00",
    python="apptainer run oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif python",
    log_directory=builds(get_output_dir),
    zen_partial=True,
)

CellXGeneStratificationClusterConfig = CellXGenePreprocessingClusterConfig(n_workers=2, processes=4, memory="1024GiB")

LocalClusterConfig = builds(LocalCluster, n_workers=1, threads_per_worker=4)
