import re
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np
import yaml

from omics_utils.pipeline.step import Step
from omics_utils.utils.columns import ColumnNames


class Limiter(Step):
    """Calculates the size of the output partitions for compatibility with the cellarium-ml dataloader."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.limit_path = self.output_path / "limits.yaml"
        self.split_path = self.input_path / "split"

    @property
    def input_step(self) -> str:
        """Name of the preceding preprocessing step."""
        return "stratification"

    @property
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        return "limits"

    def read(self) -> list[str]:
        """Get the file paths from the previous step.

        Returns
        -------
        List of file paths to prcess.
        """
        return list(self.split_path.glob("*.h5ad"))

    def transform(self, input_files: list[str]) -> dict[int, int]:
        """Compute the partition sizes for each fold from the stratification step.

        Returns
        -------
        Dictionary containing the file limits for each fold.
        """
        counts = defaultdict(dict)
        pattern = re.compile(r"fold_(\d+)_part_(\d+)\.h5ad")

        for path in input_files:
            matches = pattern.match(path.name)
            fold_id = int(matches.group(1))
            part_id = int(matches.group(2))

            with h5py.File(path, "r") as f:
                if "obs" not in f:
                    raise ValueError("File must contain key `obs`.")

                if ColumnNames.SAMPLE_ID not in f["obs"]:
                    raise ValueError(f"File must contain key `obs/{ColumnNames.SAMPLE_ID}`.")

                counts[fold_id][part_id] = len(f[f"obs/{ColumnNames.SAMPLE_ID}"])

        def get_divisions(mapping: dict[int, int]) -> list[int]:
            return np.cumsum(list(dict(sorted(mapping.items())).values())).tolist()

        return {fold_id: get_divisions(mapping) for fold_id, mapping in counts.items()}

    def write(self, limits: dict) -> None:
        """Save the computed limits to yaml.

        Args:
        ----
          limits: Dictionary containing the file limits.
        """
        with Path.open(self.limit_path, "w") as outfile:
            yaml.dump(limits, outfile, default_flow_style=False)

    def run(self) -> None:
        """Run the stratification and splitting step."""
        input_files = self.read()
        limits = self.transform(input_files)
        self.write(limits)
