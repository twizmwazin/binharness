"""binharness.aflexecutor - AFL executor for binharness."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from binharness.executor import ExecutorError, InjectableExecutor

if TYPE_CHECKING:
    from binharness.process import Process
    from binharness.target import Target


class AFLExecutor(InjectableExecutor):
    """AFL executor for binharness."""

    seed_data: Path

    def __init__(self: AFLExecutor, seed_data: Path) -> None:
        """Create an AFL executor."""
        local_dir = os.getenv("BINHARNESS_BINS_DIR")
        if local_dir is None:
            raise ExecutorError
        super().__init__(Path(local_dir) / "afl")
        self.seed_data = seed_data

    def _run_target(self: AFLExecutor, target: Target) -> Process:
        """Run a target in an environment."""
        if self.env_path is None or self._environment is None:
            raise ExecutorError
        data_dir = self._environment.get_busybox_injection().mktemp(directory=True)
        in_dir = data_dir / "in"
        self._environment.inject_files([(self.seed_data, in_dir)])
        out_dir = data_dir / "out"
        return self._environment.run_command(
            [
                self.env_path / "afl-fuzz",
                "-Q",
                "-i",
                in_dir,
                "-o",
                out_dir,
                "--",
                target.main_binary,
            ]
        )
