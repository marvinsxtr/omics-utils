from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any

import h5py
from anndata._core.anndata import AnnData
from anndata._core.sparse_dataset import BaseCompressedSparseDataset
from anndata._io.h5ad import write_sparse_as_dense
from anndata._io.specs import write_elem
from scipy import sparse


def write_h5ad(  # noqa: C901
    filepath: Path | str,
    adata: AnnData,
    *,
    as_dense: Sequence[str] = (),
    convert_strings_to_categoricals: bool = True,
    dataset_kwargs: Mapping[str, Any] = MappingProxyType({}),
    **kwargs,
) -> None:
    """Writes ``AnnData`` object to ``.h5ad`` file.

    Args:
        filepath (Path | str): The path to write to.
        adata (AnnData): The AnnData object to write.
        as_dense (Sequence[str]): Whether to write array in dense form.
        convert_strings_to_categoricals (bool): Whether to transform string annotations to categorical variables, if
            there exist less unique string annotations than values. If the number of values equals the number of
            categories, all remains unchanged.
        dataset_kwargs (Mapping[str, Any] = MappingProxyType({})): None
        **kwargs: TODO
    """
    if isinstance(as_dense, str):
        as_dense = [as_dense]
    if "raw.X" in as_dense:
        as_dense = list(as_dense)
        as_dense[as_dense.index("raw.X")] = "raw/X"
    if any(val not in {"X", "raw/X"} for val in as_dense):
        raise NotImplementedError("Currently, only ``X`` and ``raw/X`` are supported values in ``as_dense``")
    if "raw/X" in as_dense and adata.raw is None:
        raise ValueError("Cannot specify writing ``raw/X`` to dense if it doesn't exist.")

    if convert_strings_to_categoricals:
        adata.strings_to_categoricals()
        if adata.raw is not None:
            adata.strings_to_categoricals(adata.raw.var)
    dataset_kwargs = {**dataset_kwargs, **kwargs}
    filepath = Path(filepath)
    mode = "a" if adata.isbacked else "w"
    if adata.isbacked:  # close so that we can reopen below
        adata.file.close()

    with h5py.File(filepath, mode) as f:
        # TODO: Use spec writing system for this  # noqa: TD002, TD003
        # Currently can't use write_dispatched here because this function is also called to do an
        # inplace update of a backed object, which would delete "/"
        f = f["/"]  # noqa: PLW2901
        f.attrs.setdefault("encoding-type", "anndata")
        f.attrs.setdefault("encoding-version", "0.1.0")

        if "X" in as_dense and isinstance(adata.X, sparse.spmatrix | BaseCompressedSparseDataset):
            write_sparse_as_dense(f, "X", adata.X, dataset_kwargs=dataset_kwargs)
        elif not (adata.isbacked and Path(adata.filename) == Path(filepath)):
            # If adata.isbacked, X should already be up to date
            write_elem(f, "X", adata.X, dataset_kwargs=dataset_kwargs)
        if "raw/X" in as_dense and isinstance(adata.raw.X, sparse.spmatrix | BaseCompressedSparseDataset):
            write_sparse_as_dense(f, "raw/X", adata.raw.X, dataset_kwargs=dataset_kwargs)
            write_elem(f, "raw/var", adata.raw.var, dataset_kwargs=dataset_kwargs)
            write_elem(f, "raw/varm", dict(adata.raw.varm), dataset_kwargs=dataset_kwargs)
        elif adata.raw is not None:
            write_elem(f, "raw", adata.raw, dataset_kwargs=dataset_kwargs)
        write_elem(f, "obs", adata.obs, dataset_kwargs=dataset_kwargs)
        write_elem(f, "var", adata.var, dataset_kwargs=dataset_kwargs)
        write_elem(f, "obsm", dict(adata.obsm), dataset_kwargs=dataset_kwargs)
        write_elem(f, "varm", dict(adata.varm), dataset_kwargs=dataset_kwargs)
        write_elem(f, "obsp", dict(adata.obsp), dataset_kwargs=dataset_kwargs)
        write_elem(f, "varp", dict(adata.varp), dataset_kwargs=dataset_kwargs)
        write_elem(f, "layers", dict(adata.layers), dataset_kwargs=dataset_kwargs)
        write_elem(f, "uns", dict(adata.uns), dataset_kwargs=dataset_kwargs)
