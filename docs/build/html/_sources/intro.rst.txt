Introduction
============


Roadmap
*******

Contains utilities for handling larger-than-memory datasets for multiple omics modalities including

    * concatenation of multiple sub-datasets/cohorts into one larger dataset,
    * stratification and grouping by specific metadata columns,
    * assigning cross-validation folds and train/val/test splits,
    * sharding of the folds across multiple smaller-than-memory files.


Quick Start
***********

To start preprocessing (CellXGene by default), run:
::
	
    python omics_utils/preprocess.py
