from __future__ import annotations

import platform
import sys
from pathlib import Path

import pytest

ALL = {"darwin", "linux", "win32"}


def pytest_runtest_setup(item: pytest.Item) -> None:
    # Skip tests not marked as supported on the current platform
    supported_platforms = ALL.intersection(mark.name for mark in item.iter_markers())
    plat = sys.platform
    if supported_platforms and plat not in supported_platforms:
        pytest.skip(f"cannot run on platform {plat}")

    # Skip docker tests if docker is not installed
    if "docker" in list(item.iter_markers()):
        try:
            import docker
        except ImportError:
            pytest.skip("docker is not installed")
        try:
            docker.from_env()
        except docker.errors.DockerException:
            pytest.skip("docker is not running")


@pytest.fixture()
def agent_binary_linux_host_arch() -> str:
    arch = platform.machine()
    # Fixup arch for arm64
    if arch == "arm64":
        arch = "aarch64"

    expected_path = (
        Path(__file__).parent.parent.parent
        / "target"
        / f"{arch}-unknown-linux-musl"
        / "debug"
        / "bh_agent_server"
    ).absolute()
    if not expected_path.exists():
        pytest.skip("agent binary not found")
    return str(expected_path)
