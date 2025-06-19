from hydra_zen import builds

from omics_utils.configs.constants import (
    ARCHS4_OBS_COLS,
    CELLXGENE_ASSAYS,
    CELLXGENE_DISEASES,
    CELLXGENE_OBS_COLS,
    CELLXGENE_ORGANISMS,
    CELLXGENE_TISSUES,
)
from omics_utils.transforms.anndata_converter import AnnDataConverter
from omics_utils.transforms.anndata_filterer import AnnDataFilterer
from omics_utils.utils.columns import ColumnNames

CellXGeneConverterConfig = builds(
    AnnDataConverter,
    obs_cols=CELLXGENE_OBS_COLS,
    zen_partial=True,
)
Archs4ConverterConfig = builds(
    AnnDataConverter,
    obs_cols=ARCHS4_OBS_COLS,
    zen_partial=True,
)

HLCAFilterConfig = builds(dict, organism=CELLXGENE_ORGANISMS, assay=CELLXGENE_ASSAYS, is_primary_data=[False])
CellXGeneFilterConfig = builds(dict, organism=CELLXGENE_ORGANISMS, assay=CELLXGENE_ASSAYS, is_primary_data=[True])
CellXGeneSubsetFilterConfig = builds(
    dict,
    organism=CELLXGENE_ORGANISMS,
    assay=CELLXGENE_ASSAYS,
    is_primary_data=[True],
    tissue=CELLXGENE_TISSUES,
    disease=CELLXGENE_DISEASES,
)

RenameConfig = builds(dict, donor_id=ColumnNames.CASE_ID)

CellXGeneFiltererConfig = builds(
    AnnDataFilterer, genes=None, obs_filters=CellXGeneFilterConfig, obs_col_renames=RenameConfig, zen_partial=True
)
CellXGeneSubsetFiltererConfig = builds(
    AnnDataFilterer,
    genes=None,
    obs_filters=CellXGeneSubsetFilterConfig,
    obs_col_renames=RenameConfig,
    zen_partial=True,
)
HLCAFiltererConfig = builds(
    AnnDataFilterer,
    genes=None,
    obs_filters=HLCAFilterConfig,
    obs_col_renames=RenameConfig,
    zen_partial=True,
)
Archs4FiltererConfig = builds(AnnDataFilterer, genes=None, obs_filters=None, obs_col_renames=None, zen_partial=True)
