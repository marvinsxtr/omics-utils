# Omics Utils

## Roadmap

Contains utilities for handling larger-than-memory datasets for multiple omics modalities including
* Concatenation of multiple sub-datasets/cohorts into one larger dataset
* Stratification and grouping by specific metadata columns
* Assigning cross-validation folds and train/val/test splits
* Sharding of the folds across multiple smaller-than-memory files

## Quick start

To start preprocessing (CellXGene by default), run

```python
python omics_utils/preprocess.py
```

## Installation

### Virtual/Conda Environment using ``Pip``

After downloading the model repo, navigate to the ``omics-utils`` folder and install the package with

```python
pip install -e .
```

### Docker Container

The repo contains a Docker configuration, which can be utilized to develop within. An exemplary setup:

* Install ``VSCode``, including the ``Devcontainer`` extension, and ``Docker Desktop``
* Clone the repo and open it in ``VSCode``
* In the right-hand, lower corner, a message will appear: 

  ![A Devcontainer message](Bild_Devcontainer_Msg1.png)

     Click 'Reopen in Container'.
* Wait for the container building to finish. Progress can be surveilled in the ``VSCode`` "Terminal". 	
