from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster
from hydra_zen import builds

from omics_utils.utils.helpers import get_output_dir

CellXGenePartitioningClusterConfig = builds(
    SLURMCluster,
    n_workers=6,
    queue="cpu-2h",
    cores=16,
    processes=4,
    memory="512GiB",
    walltime="02:00:00",
    python="apptainer run -B /home/space/omics/datasets/cellxgene/h5ads:/srv/data oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif python",  # noqa: E501
    log_directory=builds(get_output_dir),
    zen_partial=True,
)

CellXGeneSplittingClusterConfig = CellXGenePartitioningClusterConfig(processes=2, queue="cpu-2d", walltime="48:00:00")

HLCAClusterConfig = builds(
    SLURMCluster,
    n_workers=1,
    queue="cpu-2h",
    cores=16,
    processes=4,
    memory="128GiB",
    walltime="02:00:00",
    python="apptainer run -B /home/space/omics/datasets/cellxgene/h5ads:/srv/data oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif python",  # noqa: E501
    log_directory=builds(get_output_dir),
    zen_partial=True,
)

LocalClusterConfig = builds(LocalCluster, n_workers=1, threads_per_worker=4, zen_partial=True)
