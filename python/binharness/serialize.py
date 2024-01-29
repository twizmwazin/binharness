"""binharness.serialize - Serialize and deserialize targets."""

from __future__ import annotations

import json
import tarfile
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from binharness.types.target import Target

if TYPE_CHECKING:
    from binharness.types.environment import Environment


class TargetImportError(Exception):
    """An error occurred while unpacking a target."""


def export_target(target: Target, export_path: Path) -> None:
    """Export the target to a tarball.

    This function is the inverse of import_target.
    """
    with tempfile.TemporaryDirectory() as raw_tmpdir, tarfile.open(
        export_path,
        "w:gz",
    ) as tar:
        tmpdir = Path(raw_tmpdir)
        target.environment.retrieve_files(
            [
                (target.main_binary, tmpdir / target.main_binary.name),
                *[(binary, tmpdir / binary.name) for binary in target.extra_binaries],
            ],
        )
        metadata = {
            "main_binary": target.main_binary.name,
            "extra_binaries": [binary.name for binary in target.extra_binaries],
            "args": target.args,
            "env": target.env,
        }
        (tmpdir / ".envanalysis-metadata").write_text(json.dumps(metadata))
        for file in tmpdir.iterdir():
            tar.add(file, arcname=file.name)


def import_target(environment: Environment, import_path: Path) -> Target:
    """Install a PortableTarget into the environment.

    This function is the inverse of export_target.
    """
    with tempfile.TemporaryDirectory() as raw_tempdir, tarfile.open(
        import_path,
        "r",
    ) as tar:
        tmpdir = Path(raw_tempdir)
        try:
            metadata_io = tar.extractfile(".envanalysis-metadata")
        except KeyError:
            raise TargetImportError from KeyError
        if metadata_io is None:
            raise TargetImportError
        metadata = json.loads(metadata_io.read())
        main_binary = Path(metadata["main_binary"])
        extra_binaries = [Path(binary) for binary in metadata["extra_binaries"]]
        args = metadata["args"]
        env = metadata["env"]
        for binary in [main_binary, *extra_binaries]:
            tar.extract(binary.name, path=tmpdir)
        env_install_dir = environment.get_tempdir() / main_binary.name
        environment.inject_files(
            [
                (tmpdir / binary, env_install_dir / binary)
                for binary in [main_binary, *extra_binaries]
            ],
        )
        return Target(
            environment,
            env_install_dir / main_binary,
            [env_install_dir / binary for binary in extra_binaries],
            args,
            env,
        )
