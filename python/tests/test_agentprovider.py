from __future__ import annotations

from pathlib import Path

from binharness import DevEnvironmentAgentProvider


def test_host_debug() -> None:
    provider = DevEnvironmentAgentProvider()
    assert (
        provider.get_agent_bin()
        == Path(__file__).parent.parent.parent / "target" / "debug" / "bh_agent_server"
    )
