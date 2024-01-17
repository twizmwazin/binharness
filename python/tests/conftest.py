from __future__ import annotations

import sys

import pytest

ALL = {"darwin", "linux", "win32"}


def pytest_runtest_setup(item: pytest.Item) -> None:
    supported_platforms = ALL.intersection(mark.name for mark in item.iter_markers())
    plat = sys.platform
    if supported_platforms and plat not in supported_platforms:
        pytest.skip(f"cannot run on platform {plat}")
