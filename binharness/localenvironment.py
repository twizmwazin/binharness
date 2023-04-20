"""binharness.localenvironment - A local environment."""
from __future__ import annotations

import pathlib
import shutil
import tempfile

from binharness.environment import Envirnoment
from binharness.process import Process


class LocalEnvironment(Envirnoment):
    """A local environment is the environment local to where binharness is run."""

    def __init__(self: LocalEnvironment) -> None:
        """Create a LocalEnvironment."""
        super().__init__()

    def run_command(
        self: LocalEnvironment, *args, **kwargs  # noqa: ANN002,ANN003
    ) -> Process:
        """Run a command in the environment.

        The command is run in a subprocess and the subprocess is returned. The
        subprocess is started with `subprocess.Popen` and the arguments are
        passed directly to that function.
        """
        return Process(*args, **kwargs)

    def inject_files(
        self: LocalEnvironment,
        files: list[tuple[pathlib.Path, pathlib.Path]],
    ) -> None:
        """Inject files into the environment.

        The first element of the tuple is the path to the file on the host
        machine, the second element is the path to the file in the environment.
        """
        for file in files:
            file[1].parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file[0], file[1])

    def retrieve_files(
        self: LocalEnvironment,
        files: list[tuple[pathlib.Path, pathlib.Path]],
    ) -> None:
        """Retrieve files from the environment.

        The first element of the tuple is the path to the file in the
        environment, the second element is the path to the file on the host
        machine.
        """
        for file in files:
            shutil.copy(file[0], file[1])

    def get_tempdir(self: LocalEnvironment) -> pathlib.Path:
        """Get a Path for a temporary directory."""
        return pathlib.Path(tempfile.gettempdir())
