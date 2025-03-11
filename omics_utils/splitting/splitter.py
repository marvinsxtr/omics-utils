from abc import ABC, abstractmethod

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, StratifiedShuffleSplit

from omics_utils.utils.columns import ColumnNames


class Splitter(ABC):
    """
    Facilitates splitting of datasets into multiple folds."""

    @abstractmethod
    def split(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate a new split of a metadata `DataFrame` into folds.

        Parameters
        ----------
        df: pd.DataFrame
	    ``DataFrame`` to be split into folds.

        Returns
        -------
        ``DataFrame`` containing the fold indices in a new ``ColumnNames.FOLD`` column.
        """
        ...


class StratifiedSplitter(Splitter):
    """Split a dataset into stratified folds according to a subset of metadata columns."""

    def __init__(
        self,
        sklearn_splitter: StratifiedKFold | StratifiedShuffleSplit | StratifiedGroupKFold,
        stratification_columns: list[str] | None = None,
        grouping_column: list[str] | None = None,
    ) -> None:
        """
	Creates an instance of a stratified splitter.
	
	Parameters
        ----------
        sklearn_splitter: StratifiedKFold | StratifiedShuffleSplit | StratifiedGroupKFold 
	    Sklearn splitter to use for the split.
        stratification_columns:  list[str] | None = None 
	    Subset of columns defining the metadata subset to stratify by.
        grouping_column: list[str] | None = None
	    Column containing the metadata to group by.
        """
        self.sklearn_splitter = sklearn_splitter
        self.n_splits = 2 if isinstance(sklearn_splitter, StratifiedShuffleSplit) else sklearn_splitter.get_n_splits()
        self.stratification_columns = stratification_columns
        self.grouping_column = grouping_column

    def _validate_input_df(self, df: pd.DataFrame) -> None:
        """Validate the input ``DataFrame`` column data types and subset."""
        strat_cols = self.stratification_columns
        if strat_cols is not None and (not set(strat_cols).issubset(df.columns)):
            raise ValueError(f"The `stratification_columns` have to be all in `df`. Got {strat_cols}.")

        group_col = self.grouping_column
        if group_col is not None and (not set(group_col).issubset(df.columns)):
            raise ValueError(f"The `grouping_column` has to be in `df`. Got {group_col}.")

    def split(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform a stratified split of a ``DataFrame`` into folds.

        Parameters
        ----------
        df: pd.DataFrame 
	    A ``DataFrame`` containing metadata to stratify by.

        Returns
        -------
        A ``DataFrame`` containing the fold indices in the ``ColumnNames.FOLD`` column.
        """
        self._validate_input_df(df)

        strata_df = df[self.stratification_columns].copy() if self.stratification_columns is not None else df
        groups = df[self.grouping_column] if self.grouping_column is not None else None

        aggregated_strata = strata_df.agg(lambda x: "-".join(map(str, x)), axis=1)

        df[ColumnNames.FOLD] = -1
        fold_column_idx = df.columns.get_loc(ColumnNames.FOLD)

        split_iterator = self.sklearn_splitter.split(X=aggregated_strata, y=aggregated_strata, groups=groups)

        for fold_idx, (train_idx, test_idx) in enumerate(split_iterator):
            df.iloc[test_idx, fold_column_idx] = fold_idx

            if isinstance(self.sklearn_splitter, StratifiedShuffleSplit):
                df.iloc[train_idx, fold_column_idx] = 1

        return df

