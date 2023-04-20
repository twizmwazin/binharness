"""binharness.process - A process running in an environment."""
from __future__ import annotations

import subprocess


class Process(subprocess.Popen):
    """A process running in an environment.

    TODO: This class is a stub. It should be implemented. Inheriting from
    subprocess.Popen directly is not a good idea for environments other than the
    local environment.
    """

    def __init__(self: Process, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        """Create a Process."""
        super().__init__(*args, **kwargs)
