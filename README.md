# 🧬 Omics Utils

A modern toolkit for handling larger-than-memory datasets across multiple omics modalities using **hydra-zen** and **dask** on a Slurm cluster with Docker/Apptainer containerization.

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

- [🔑 Container Registry Authentication](#container-registry-authentication)
- [🐳 Container Setup](#container-setup)
  - [Option 1: Apptainer (Slurm Cluster)](#option-1-apptainer-slurm-cluster)
  - [Option 2: Docker (Local Machine)](#option-2-docker-local-machine)
- [🧬 Running Preprocessing](#running-preprocessing)
- [📦 Package Management](#package-management)
- [👥 Contributions](#contributions)

## 🔑 Container Registry Authentication

### Generate Token

1. Create a new GitHub token at [Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens) with:
   - `read:packages` permission
   - `write:packages` permission

### Log In

With Apptainer:
```bash
apptainer remote login --username <your GitHub username> docker://ghcr.io
```

With Docker:
```bash
docker login ghcr.io -u <your GitHub username>
```

When prompted, enter your token as the password.

## 🐳 Container Setup

Choose one of the following methods to set up your environment:

### Option 1: Apptainer (Slurm Cluster)

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
   apptainer run --nv --writable-tmpfs oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif code tunnel
   ```

   > 💡 You can specify a version tag (e.g., `v0.0.1`) instead of `latest`. Available versions are listed at [GitHub Container Registry](https://github.com/bifold-pathomics/omics-utils/pkgs/container/omics-utils).

   In VSCode press `Shift+Alt+P` (Windows/Linux) or `Shift+Cmd+P` (Mac), type "connect to tunnel", select GitHub and select your named node on the cluster. Your IDE is now connected to the cluster.

   To open a shell in the container on the cluster:
   ```bash
   apptainer run --nv --writable-tmpfs oras://ghcr.io/bifold-pathomics/omics-utils:latest-sif /bin/bash
   ```

   > 💡 This may take a few minutes on the first run as the container image is downloaded.

### Option 2: Docker (Local Machine)

1. **Install VSCode Dev Containers Extension**

   First, install the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension in VSCode.

2. **Open the Repository in the Dev Container**

   Click the `Reopen in Container` button in the pop-up that appears once you open the repository in VSCode.

   Alternatively, open the command palette in VSCode by pressing `Shift+Alt+P` (Windows/Linux) or `Shift+Cmd+P` (Mac), and type `Dev Containers: Reopen in Container`.

## 🧬 Running Preprocessing

> Make sure you followed the previous sections beforehand and run these commands in the container.

The preprocessing pipeline supports multiple omics modalities:

### CellXGene Preprocessing

```bash
python omics_utils/preprocess.py
```

### Methylation Preprocessing

```bash
python omics_utils/preprocess.py preprocessor=methylation
```

## 📦 Package Management

1. **Update dependencies**

   This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management.

   Inside the container (!):
   ```bash
   # Add a specific package
   uv add <package-name>

   # Update all dependencies from pyproject.toml
   uv sync
   ```

2. **Commit changes** to the repository:

   Use tags for versioning:

   ```bash
   git add pyproject.toml uv.lock 
   git commit -m "Updated dependencies"
   git tag v0.0.1
   git push && git push --tags
   ```

3. **Use the updated image**:

   The GitHub Actions workflow automatically builds a new image when changes are pushed.

   With Apptainer:
   ```bash
   apptainer run --nv --writable-tmpfs oras://ghcr.io/bifold-pathomics/omics-utils:v0.0.1-sif /bin/bash
   ```

   With Docker:
   ```bash
   docker run -it --rm --platform=linux/amd64 ghcr.io/bifold-pathomics/omics-utils:v0.0.1 /bin/bash
   ```

## 👥 Contributions

Contributions to this project are very welcome! Feel free to open a PR or reach out with suggestions.
