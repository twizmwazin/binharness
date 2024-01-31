"""binharness.types.stat - Represents file statistics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os

    import bh_agent_client


@dataclass
class FileStat:
    """Represents file statistics."""

    mode: int
    """File mode."""
    uid: int
    """User ID."""
    gid: int
    """Group ID."""
    size: int
    """File size."""
    atime: int
    """Access time."""
    mtime: int
    """Modification time."""
    ctime: int
    """Creation time."""

    @staticmethod
    def from_os(stat: os.stat_result) -> FileStat:
        """Create a FileStat from an os.stat_result."""
        return FileStat(
            mode=stat.st_mode,
            uid=stat.st_uid,
            gid=stat.st_gid,
            size=stat.st_size,
            atime=stat.st_atime_ns,
            mtime=stat.st_mtime_ns,
            ctime=stat.st_ctime_ns,
        )

    @staticmethod
    def from_agent(stat: bh_agent_client.FileStat) -> FileStat:
        """Create a FileStat from a binharness_agent_client.FileStat."""
        return FileStat(
            mode=stat.mode,
            uid=stat.uid,
            gid=stat.gid,
            size=stat.size,
            atime=stat.atime,
            mtime=stat.mtime,
            ctime=stat.ctime,
        )
