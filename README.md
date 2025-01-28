# Omics Utils

Contains utilities for handling larger-than-memory datasets for multiple omics modalities including
* Concatenation of multiple sub-datasets/cohorts into one larger dataset
* Stratification and grouping by specific metadata columns
* Assigning cross-validation folds and train/val/test splits
* Sharding of the folds across multiple smaller-than-memory files
