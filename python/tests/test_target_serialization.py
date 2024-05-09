from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from binharness import (
    Environment,
    NullExecutor,
    Target,
    TargetImportError,
    export_target,
    import_target,
)


def test_local_target_export(env: Environment) -> None:
    target = Target(env, Path("/usr/bin/true"))
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        export_target(target, tmpdir / "test_export.zip")


def test_local_target_import(env: Environment) -> None:
    target = Target(env, Path("/usr/bin/true"))
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        assert tmpdir.exists()
        assert tmpdir.is_dir()
        export_path = tmpdir / "test_export.zip"
        export_target(target, export_path)
        new_target = import_target(env, export_path)
    assert new_target.main_binary.name == target.main_binary.name
    executor = NullExecutor()
    assert executor.run_target(new_target).wait() == 0


def test_local_target_import_without_metadata(env: Environment) -> None:
    target = Target(env, Path("/usr/bin/true"))
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        export_target(target, tmpdir / "test_export.zip")
        with (
            zipfile.ZipFile(tmpdir / "test_export.zip", "r") as old_zip,
            zipfile.ZipFile(
                tmpdir / "test_export_modified.zip",
                "w",
            ) as new_zip,
        ):
            for member in old_zip.infolist():
                if member.filename != ".bh-target-metadata":
                    new_zip.writestr(member, old_zip.read(member.filename))
        with pytest.raises(TargetImportError):
            import_target(env, tmpdir / "test_export_modified.zip")


def test_local_target_import_invalid_metadata_archive(env: Environment) -> None:
    target = Target(env, Path("/usr/bin/true"))
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        export_target(target, tmpdir / "test_export.zip")
        with (
            zipfile.ZipFile(tmpdir / "test_export.zip", "r") as old_zip,
            zipfile.ZipFile(
                tmpdir / "test_export_modified.zip",
                "w",
            ) as new_zip,
        ):
            for info in old_zip.infolist():
                if info.filename != ".bh-target-metadata":
                    new_zip.writestr(info.filename, old_zip.read(info))
            new_zip.writestr(".bh-target-metadata/", "")
        with pytest.raises(TargetImportError):
            import_target(env, tmpdir / "test_export_modified.zip")
