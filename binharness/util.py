"""binharness.util - Utility functions for binharness."""
from __future__ import annotations

import shlex
from pathlib import Path
from typing import Sequence


def normalize_args(*args: Path | str | Sequence[Path | str]) -> Sequence[str]:
    """Normalize arguments to a list of strings."""
    # Handle case with single quoted string
    if len(args) == 1 and isinstance(args[0], str):
        return shlex.split(args[0])

    flattened_args: list[str] = []
    for arg in args:
        if isinstance(arg, (str, Path)):
            flattened_args.append(str(arg))
        elif isinstance(arg, (list, set, tuple)):
            flattened_args.extend(str(a) for a in arg)
    return flattened_args


def join_normalized_args(args: Sequence[str]) -> str:
    """Convert a list of normalized arguments to a string."""
    return " ".join(shlex.quote(arg) for arg in args)
