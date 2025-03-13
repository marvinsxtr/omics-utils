# 🧬 Omics Utils

A modern toolkit for handling larger-than-memory datasets across multiple omics modalities using **dask**, **hydra-zen** and **wandb** on a Slurm cluster with Docker/Apptainer containerization.

<div align="center">

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue.svg)](https://www.docker.com/)
[![Hydra Zen](https://img.shields.io/badge/Hydra%20Zen-Config-green.svg)](https://github.com/mit-ll-responsible-ai/hydra-zen)
[![Dask](https://img.shields.io/badge/Dask-Parallelization-orange.svg)](https://www.dask.org/)

</div>

## 🌟 Key Features

- 🧪 Concatenation of multiple sub-datasets/cohorts into one larger dataset
- 🔍 Stratification and grouping by specific metadata columns
- 🔀 Assigning cross-validation folds and train/val/test splits
- 💾 Sharding of the folds across multiple smaller-than-memory files
- 🚀 Dask + Slurm integration for efficient parallelization
- 🧩 Reproducibility and modular type-checked configs via [hydra-zen](https://github.com/mit-ll-responsible-ai/hydra-zen)

## 📋 Table of Contents

- [🧬 Running Preprocessing](#-running-preprocessing)
- [🐳 Container Setup](#-container-setup)
  - [Option 1: Apptainer (Cluster)](#option-1-apptainer-cluster)
  - [Option 2: Docker (Local Machine)](#option-2-docker-local-machine)
- [📦 Package Management](#-package-management)
- [👥 Contributions](#-contributions)

## 🐳 Container Setup

Choose one of the following methods to set up your environment:

### Option 1: Apptainer (Cluster)

1. **Install VSCode Remote Tunnels Extension**

   First, install the [Remote Tunnels](https://marketplace.visualstudio.com/items?itemName=ms-vscode.remote-server) extension in VSCode.

2. **Connect to compute resources**

   For CPU resources:
   ```bash
   srun --partition=cpu-2h --pty bash
   ```
   
   For GPU resources:
   ```bash
   srun --partition=gpu-2h --gpus-per-task=1 --pty bash
   ```

3. **Launch container**

   To open a tunnel to connect your local VSCode to the container on the cluster:
   ```bash
   apptainer run --nv --writable-tmpfs oras://ghcr.io/yourusername/omics-utils:latest-sif code tunnel
   ```

   In VSCode press `Shift+Alt+P` (Windows/Linux) or `Shift+Cmd+P` (Mac), type "connect to tunnel", select GitHub and select your named node on the cluster. Your IDE is now connected to the cluster.

   To open a shell in the container on the cluster:
   ```bash
   apptainer run --nv --writable-tmpfs oras://ghcr.io/yourusername/omics-utils:latest-sif /bin/bash
   ```

### Option 2: Docker (Local Machine)

1. **Install VSCode Dev Containers Extension**

   First, install the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension in VSCode.

2. **Open the Repository in the Dev Container**

   Click the `Reopen in Container` button in the pop-up that appears once you open the repository in VSCode.

   Alternatively, open the command palette in VSCode by pressing `Shift+Alt+P` (Windows/Linux) or `Shift+Cmd+P` (Mac), and type `Dev Containers: Reopen in Container`.

## 📦 Package Management

This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management.

### Adding or Updating Dependencies

Inside the container:
```bash
# Add a specific package
uv add <package-name>

# Update all dependencies from pyproject.toml
uv sync
```

## 🧬 Running Preprocessing

The preprocessing pipeline supports multiple omics modalities:

### CellXGene Preprocessing

```bash
python omics_utils/preprocess.py preprocessor=cellxgene
```

### Methylation Preprocessing

```bash
python omics_utils/preprocess.py preprocessor=methylation
```

## 👥 Contributions

Contributions to this project are very welcome! Feel free to open a PR or reach out with suggestions.