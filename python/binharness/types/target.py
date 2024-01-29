"""binharness.types.target - A target in an environment."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from binharness import Environment


class Target:
    """A Target is a representation of a target in an environment."""

    environment: Environment
    main_binary: Path
    extra_binaries: list[Path]
    args: list[str]
    env: dict[str, str]

    def __init__(  # noqa: PLR0913
        self: Target,
        environment: Environment,
        main_binary: Path,
        extra_binaries: list[Path] | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        """Create a Target."""
        self.environment = environment
        self.main_binary = main_binary
        self.extra_binaries = extra_binaries if extra_binaries is not None else []
        self.args = args if args is not None else []
        self.env = env if env is not None else {}
