"""binharness.util - Utility functions for binharness."""

from __future__ import annotations

import random
import shlex
import string
from pathlib import Path
from typing import TYPE_CHECKING, Generator, Sequence

if TYPE_CHECKING:
    from binharness.types.io import IO


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


def read_lines(file: IO[bytes]) -> Generator[bytes, None, None]:
    """Read lines from a file."""
    buffer = b""
    while True:
        chunk = file.read(4096)
        if not chunk:
            if buffer:
                yield buffer
            break

        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            yield line + b"\n"


def generate_random_suffix(n: int = 6) -> str:
    """Generate a random suffix."""
    return "".join(random.choices(string.ascii_letters, k=n))  # noqa: S311
