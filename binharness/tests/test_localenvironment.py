from __future__ import annotations

import pathlib
import subprocess
import tempfile

from binharness.localenvironment import LocalEnvironment


def test_run_command() -> None:
    env = LocalEnvironment()
    proc = env.run_command(["echo", "hello"], stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()
    assert proc.returncode == 0
    assert stdout == b"hello\n"


def test_inject_files() -> None:
    env = LocalEnvironment()
    env_temp = env.get_tempdir()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        file = tmp_path / "test.txt"
        file.write_text("hello")
        env.inject_files([(file, env_temp / "test.txt")])

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_file = pathlib.Path(tmp_dir) / "test.txt"
        env.retrieve_files([(env_temp / "test.txt", local_file)])
        assert local_file.read_text() == "hello"


def test_get_tempdir() -> None:
    env = LocalEnvironment()
    assert env.get_tempdir() == pathlib.Path(tempfile.gettempdir())
