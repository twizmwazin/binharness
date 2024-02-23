"""binharness.serialize - Serialize and deserialize targets."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from binharness.types.target import Target

if TYPE_CHECKING:
    from binharness.types.environment import Environment

_ZIP_UNIX_SYSTEM = 3
_META_FILENAME = ".bh-target-metadata"


class TargetImportError(Exception):
    """An error occurred while unpacking a target."""


def export_target(target: Target, export_path: Path) -> None:
    """Export the target to a tarball.

    This function is the inverse of import_target.
    """
    with tempfile.TemporaryDirectory() as raw_tmpdir, zipfile.ZipFile(
        export_path, "w"
    ) as archive:
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
        (tmpdir / _META_FILENAME).write_text(json.dumps(metadata))
        for file in tmpdir.iterdir():
            archive.write(file, arcname=file.name)


def import_target(environment: Environment, import_path: Path) -> Target:
    """Install a PortableTarget into the environment.

    This function is the inverse of export_target.
    """
    with tempfile.TemporaryDirectory() as raw_tempdir, zipfile.ZipFile(
        import_path
    ) as zip_file:
        tmpdir = Path(raw_tempdir)
        try:
            metadata_io = zip_file.read(_META_FILENAME)
        except KeyError:
            raise TargetImportError from KeyError
        if metadata_io is None:
            raise TargetImportError
        metadata = json.loads(metadata_io)
        main_binary = Path(metadata["main_binary"])
        extra_binaries = [Path(binary) for binary in metadata["extra_binaries"]]
        args = metadata["args"]
        env = metadata["env"]
        to_extract = [str(p) for p in [main_binary, *extra_binaries]]
        for info in zip_file.infolist():
            if info.filename in to_extract:
                extracted_path = zip_file.extract(info.filename, tmpdir)
                # Restore permissions, https://stackoverflow.com/questions/42326428/
                if info.create_system == _ZIP_UNIX_SYSTEM:
                    unix_attributes = info.external_attr >> 16
                    if unix_attributes:
                        Path(extracted_path).chmod(unix_attributes)

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


def transport_target(target: Target, new_env: Environment) -> Target:
    """Transport a target to a new environment by exporting and importing it."""
    with tempfile.NamedTemporaryFile() as export_file:
        export_target(target, Path(export_file.name))
        return import_target(new_env, Path(export_file.name))
