from __future__ import annotations

import tarfile
import tempfile
from pathlib import Path

import pytest

from binharness.executor import NullExecutor
from binharness.localenvironment import LocalEnvironment
from binharness.serialize import TargetImportError, export_target, import_target
from binharness.target import Target


def test_local_target_export() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("/bin/true"))
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        export_target(target, tmpdir / "test_export.tar.gz")


def test_local_target_import() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("/bin/true"))
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        export_target(target, tmpdir / "test_export.tar.gz")
        new_target = import_target(env, tmpdir / "test_export.tar.gz")
    assert new_target.main_binary.name == target.main_binary.name
    executor = NullExecutor()
    assert executor.run_target(new_target).wait() == 0


def test_local_target_import_without_metadata() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("/bin/true"))
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        export_target(target, tmpdir / "test_export.tar.gz")
        with tarfile.open(tmpdir / "test_export.tar.gz", "r") as old_tar, tarfile.open(
            tmpdir / "test_export_modified.tar.gz",
            "w:gz",
        ) as new_tar:
            for member in old_tar.getmembers():
                if member.name != ".envanalysis-metadata":
                    new_tar.addfile(member, old_tar.extractfile(member))
        with pytest.raises(TargetImportError):
            import_target(env, tmpdir / "test_export_modified.tar.gz")


def test_local_target_import_invalid_metadata_archive() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("/bin/true"))
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        export_target(target, tmpdir / "test_export.tar.gz")
        with tarfile.open(tmpdir / "test_export.tar.gz", "r") as old_tar, tarfile.open(
            tmpdir / "test_export_modified.tar.gz",
            "w:gz",
        ) as new_tar:
            for member in old_tar.getmembers():
                if member.name != ".envanalysis-metadata":
                    new_tar.addfile(member, old_tar.extractfile(member))
                bad_metadata = tarfile.TarInfo(".envanalysis-metadata")
                bad_metadata.type = tarfile.DIRTYPE
                new_tar.addfile(bad_metadata)
        with pytest.raises(TargetImportError):
            import_target(env, tmpdir / "test_export_modified.tar.gz")
