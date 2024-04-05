"""binharness - A library for analyzing a program in its environment."""

from __future__ import annotations

__version__ = "0.1.1"

from binharness.agentenvironment import AgentConnection, AgentEnvironment
from binharness.agentprovider import AgentProvider, DevEnvironmentAgentProvider
from binharness.common import BusyboxInjection
from binharness.localenvironment import LocalEnvironment
from binharness.serialize import (
    TargetImportError,
    export_target,
    import_target,
    transport_target,
)
from binharness.types import (
    IO,
    Environment,
    ExecutableInjection,
    Executor,
    ExecutorEnvironmentMismatchError,
    ExecutorError,
    InjectableExecutor,
    Injection,
    InjectionAlreadyInstalledError,
    InjectionError,
    InjectionNotInstalledError,
    NullExecutor,
    Process,
    Target,
)

__all__ = [
    "AgentConnection",
    "AgentEnvironment",
    "AgentProvider",
    "BusyboxInjection",
    "DevEnvironmentAgentProvider",
    "Environment",
    "ExecutableInjection",
    "Executor",
    "ExecutorEnvironmentMismatchError",
    "ExecutorError",
    "IO",
    "InjectableExecutor",
    "Injection",
    "InjectionAlreadyInstalledError",
    "InjectionError",
    "InjectionNotInstalledError",
    "LocalEnvironment",
    "NullExecutor",
    "Process",
    "Target",
    "TargetImportError",
    "export_target",
    "import_target",
    "transport_target",
]
