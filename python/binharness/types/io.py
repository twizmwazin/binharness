"""binharness.types.io - Type definition for file-like objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, AnyStr, ContextManager, Protocol

if TYPE_CHECKING:
    from types import TracebackType


class IO(ContextManager["IO[AnyStr]"], Protocol[AnyStr]):
    """A file-like object."""

    def close(self: IO[AnyStr]) -> None:
        """Close the file."""

    @property
    def closed(self: IO[AnyStr]) -> bool:
        """Whether the file is closed."""

    def flush(self: IO[AnyStr]) -> None:
        """Flush the file."""

    def read(self: IO[AnyStr], n: int = -1) -> AnyStr:
        """Read n bytes from the file."""

    def readable(self: IO[AnyStr]) -> bool:
        """Whether the file is readable."""

    def readline(self: IO[AnyStr], limit: int = -1) -> AnyStr:
        """Read a line from the file."""

    def readlines(self: IO[AnyStr], hint: int = -1) -> list[AnyStr]:
        """Read lines from the file."""

    def seek(self: IO[AnyStr], offset: int, whence: int = 0) -> int | None:
        """Seek to a position in the file."""

    def seekable(self: IO[AnyStr]) -> bool:
        """Whether the file is seekable."""

    def tell(self: IO[AnyStr]) -> int:
        """Get the current position in the file."""

    def writable(self: IO[AnyStr]) -> bool:
        """Whether the file is writable."""

    def write(self: IO[AnyStr], s: AnyStr) -> int | None:
        """Write to the file."""

    def writelines(self: IO[AnyStr], lines: list[AnyStr]) -> None:
        """Write lines to the file."""

    def __enter__(self: IO[AnyStr]) -> IO[AnyStr]:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(
        self: IO[AnyStr],
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the runtime context and close the file if it's open."""
        if not self.closed:
            self.close()

    def set_blocking(self: IO[AnyStr], blocking: bool) -> None:  # noqa: FBT001
        """Set the file to blocking or non-blocking mode."""
        raise NotImplementedError
