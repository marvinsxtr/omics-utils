from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Step(ABC):
    """Base preprocessing step in a modular ETL pipeline. Also see ``PreprocessingPipeline``."""

    def __init__(self, base_dir: str) -> None:
        """Initializes an instance of a base preprocessing step.

        Args:
            base_dir (str): Folder where a subfolder is created for each preprocessing step.
        """
        base_path = Path(base_dir)

        input_path = base_path / self.input_step if self.input_step is not None else None
        output_path = base_path / self.output_step

        self.base_path = base_path
        self.input_path = input_path
        self.output_path = output_path

    @property
    @abstractmethod
    def input_step(self) -> str | None:
        """Name of the preprocessing step preceding this one or ``None`` if this is the first."""
        ...

    @property
    @abstractmethod
    def output_step(self) -> str:
        """Name of this preprocessing step."""
        ...

    @abstractmethod
    def read(self) -> Any:
        """Read the data from the previous step or the input data.

        Returns:
            The data ready for transformation.
        """
        ...

    @abstractmethod
    def transform(self, *args: Any) -> Any:
        """Transform the data.

	    Args:
    	    args (Any ): The input data.

	    Returns:
    	    The transformed output.
 	    """
        ...

    @abstractmethod
    def write(self, *args: Any) -> None:
        """Save the result of the transformation.

        Args:
            args (Any ): The transformed data.
        """
        ...

    @abstractmethod
    def run(self) -> None:
        """Run the whole preprocessing step by sequentially running ``read``, ``transform`` and ``write``."""
        ...
