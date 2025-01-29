from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


class HDF5Splitter:
    """A utility class for splitting HDF5 files into stratified train/test sets.

    This class handles the splitting of HDF5 files while maintaining the distribution
    of specified columns and respecting group boundaries to prevent data leakage.
    """

    def __init__(
        self,
        input_path: str,
        output_dir: str,
        stratify_cols: list[str],
        group_col: str,
        seed: int,
        num_splits: int = 5,
    ) -> None:
        """Initializes the HDF5Splitter.

        Args:
            input_path: Path to the input .h5 file.
            output_dir: Directory to save the splits.
            stratify_cols: Columns to use for stratification.
            group_col: Column to use for grouping.
            seed: Random seed.
            num_splits: Number of splits for cross-validation. Default is 5.
        """
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.stratify_cols = stratify_cols
        self.group_col = group_col
        self.seed = seed
        self.num_splits = num_splits

    def load_data(self) -> None:
        """Loads the data from the HDF5 file."""
        with h5py.File(self.input_path, "r") as f:
            self.features = np.array(f["beta_mat"], dtype=np.float32)
            sample_info = f["sample_info"]

            # Convert sample_info to a DataFrame keeping only relevant columns
            fields = [*self.stratify_cols, self.group_col]

            metadata = {}
            for field in fields:
                values = sample_info.fields([field])[:]
                metadata[field] = [x[0].decode("utf-8") for x in values.tolist()]

            self.metadata = pd.DataFrame(metadata)

    def split_data(self) -> None:
        """Splits the data into train_val and test sets."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        test_dir = self.output_dir / "test"
        test_dir.mkdir(exist_ok=True)

        stratify_values = self.metadata[self.stratify_cols].astype(str).agg("_".join, axis=1)
        groups = self.metadata[self.group_col]

        splitter = StratifiedGroupKFold(n_splits=self.num_splits, shuffle=True, random_state=self.seed)

        # Get train_val and test split
        train_val_idx, test_idx = next(iter(splitter.split(self.features, stratify_values, groups)))
        self.train_val_features = self.features[train_val_idx]
        self.train_val_metadata = self.metadata.iloc[train_val_idx].reset_index(drop=True)
        test_path = test_dir / "test.h5ad"
        self._save_fold(test_path, test_idx, self.metadata, self.features)

    def create_folds(self) -> None:
        """Creates cross-validation folds from the train_val data."""
        train_val_dir = self.output_dir / "train_val"
        train_val_dir.mkdir(exist_ok=True)

        stratify_values = self.train_val_metadata[self.stratify_cols].astype(str).agg("_".join, axis=1)
        groups = self.train_val_metadata[self.group_col]

        splitter = StratifiedGroupKFold(n_splits=self.num_splits, shuffle=True, random_state=self.seed)

        for fold, (_, val_idx) in enumerate(splitter.split(self.train_val_features, stratify_values, groups)):
            assert len(val_idx) > 0, (
                f"Fold {fold} is empty. Reduce the number of folds or change stratification/grouping criteria."
            )

            fold_path = train_val_dir / f"fold_{fold}.h5ad"
            self._save_fold(fold_path, val_idx, self.train_val_metadata, self.train_val_features)

    def _save_fold(self, path: str, indices: np.ndarray, metadata: pd.DataFrame, features: np.ndarray) -> None:
        """Saves the selected fold or split as an AnnData object."""
        features_split = features[indices]
        metadata_split = metadata.iloc[indices].reset_index(drop=True)

        # Convert the index to string because AnnData requires it
        metadata_split.index = metadata_split.index.astype(str)

        # Create an AnnData object
        adata = ad.AnnData(X=features_split, obs=metadata_split)

        # Save the AnnData object as .h5ad
        adata.write(path)


# Example usage
if __name__ == "__main__":
    input_path = "../datasets/LUSC_v2-0.h5"
    output_dir = "../datasets/splits"
    stratify_cols = ["organ"]
    group_col = "study_ID"
    seed = 1

    splitter = HDF5Splitter(input_path, output_dir, stratify_cols, group_col, seed)
    splitter.load_data()
    splitter.split_data()
    splitter.create_folds()
