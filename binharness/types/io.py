"""binharness.types.io - Type definition for file-like objects."""
from __future__ import annotations

from typing import AnyStr, Protocol


class IO(Protocol[AnyStr]):
    """A file-like object."""

    def close(self: IO) -> None:
        """Close the file."""

    @property
    def closed(self: IO) -> bool:
        """Whether the file is closed."""

    def flush(self: IO) -> None:
        """Flush the file."""

    def read(self: IO, n: int = -1) -> AnyStr:
        """Read n bytes from the file."""

    def readable(self: IO) -> bool:
        """Whether the file is readable."""

    def readline(self: IO, limit: int = -1) -> AnyStr:
        """Read a line from the file."""

    def readlines(self: IO, hint: int = -1) -> list[AnyStr]:
        """Read lines from the file."""

    def seek(self: IO, offset: int, whence: int = 0) -> int | None:
        """Seek to a position in the file."""

    def seekable(self: IO) -> bool:
        """Whether the file is seekable."""

    def tell(self: IO) -> int:
        """Get the current position in the file."""

    def writable(self: IO) -> bool:
        """Whether the file is writable."""

    def write(self: IO, s: AnyStr) -> int | None:
        """Write to the file."""

    def writelines(self: IO, lines: list[AnyStr]) -> None:
        """Write lines to the file."""
