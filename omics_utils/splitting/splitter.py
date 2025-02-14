from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold

from omics_utils.utils.columns import ColumnNames


class Splitter(ABC):
    """Facilitates splitting of datasets into multiple folds."""

    def __init__(
        self,
        num_folds: int,
        shuffle: bool = False,
        seed: int | None = None,
    ) -> None:
        """Args:
        ----
          num_folds: The number of folds to split the data into.
          shuffle: Whether to shuffle the data before assigning the folds.
          seed: Seed for reproducibility, only needed if `shuffle` is True.
        """
        self.num_folds = num_folds
        self.shuffle = shuffle
        self.seed = seed

    @abstractmethod
    def split(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate a new split of a metadata `DataFrame` into folds.

        Args:
        ----
          df: `DataFrame` to be split into folds.

        Returns:
        -------
        `DataFrame` containing the fold indices in a new `ColumnNames.FOLD` column.
        """
        ...


class StratifiedSplitter(Splitter):
    """Split a dataset into stratified folds according to a subset of metadata columns."""

    def __init__(
        self,
        num_folds: int,
        stratification_columns: list[str] | None = None,
        **kwargs,
    ) -> None:
        """Args:
        ----
          num_folds: Number of folds.
          stratification_columns: Subset of columns defining the metadata subset to stratify by.
        """
        super().__init__(num_folds, **kwargs)
        self.stratification_columns = stratification_columns
        self.skf = StratifiedKFold(self.num_folds, shuffle=self.shuffle, random_state=self.seed)

    def _validate_input_df(self, df: pd.DataFrame) -> None:
        """Validate the input `DataFrame` column data types and subset."""
        strat_cols = self.stratification_columns
        if strat_cols is not None and (not set(strat_cols).issubset(df.columns)):
            raise ValueError(f"The `stratification_columns` have to be all in `df`. Got {strat_cols}.")

    def split(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform a stratified split of a `DataFrame` into folds.

        Args:
        ----
          df: A `DataFrame` containing metadata to stratify by.

        Returns:
        -------
        A `DataFrame` containing the fold indices in the `ColumnNames.FOLD` column.
        """
        self._validate_input_df(df)

        if self.stratification_columns is not None:
            strata_df = df[self.stratification_columns].copy()

        aggregated_strata = strata_df.agg(lambda x: "-".join(map(str, x)), axis=1)

        df[ColumnNames.FOLD] = -1
        fold_column_idx = df.columns.get_loc(ColumnNames.FOLD)

        split_iterator = self.skf.split(X=aggregated_strata, y=aggregated_strata)

        for fold_idx, (_, test_idx) in enumerate(split_iterator):
            df.iloc[test_idx, fold_column_idx] = fold_idx

        return df


class RandomSplitter(Splitter):
    """Split a dataset into random folds."""

    def __init__(
        self,
        num_folds: int,
        **kwargs,
    ) -> None:
        """Args:
        ----
          num_folds: Number of folds.
        """
        super().__init__(num_folds, **kwargs)
        self.kf = KFold(n_splits=self.num_folds, shuffle=self.shuffle, random_state=self.seed)

    def split(self, df: pd.DataFrame) -> pd.DataFrame:
        """Randomly split a `DataFrame` into folds.

        Args:
        ----
          df: `Dataframe` to split into random folds.

        Returns:
        -------
        `Dataframe` containing the fold indices in a new `ColumnNames.FOLD` column.
        """
        df[ColumnNames.FOLD] = -1
        fold_column_idx = df.columns.get_loc(ColumnNames.FOLD)
        split_iterator = self.kf.split(df.to_numpy(dtype=np.float32))

        for fold_idx, (_, test_idx) in enumerate(split_iterator):
            df.iloc[test_idx, fold_column_idx] = fold_idx

        return df
