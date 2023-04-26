from __future__ import annotations

from pathlib import Path

from binharness.util import join_normalized_args, normalize_args


def test_single_string() -> None:
    assert normalize_args("test") == ["test"]


def test_single_quoted_string() -> None:
    assert normalize_args("'test'") == ["test"]


def test_single_quoted_string_with_spaces() -> None:
    assert normalize_args("'test test'") == ["test test"]


def test_path() -> None:
    assert normalize_args(Path("test")) == ["test"]


def test_list() -> None:
    assert normalize_args(["one", "two"]) == ["one", "two"]


def test_two_lists() -> None:
    assert normalize_args(["one", "two"], ["three", "four"]) == [
        "one",
        "two",
        "three",
        "four",
    ]


def test_list_followed_by_string() -> None:
    assert normalize_args(["one", "two"], "three") == [
        "one",
        "two",
        "three",
    ]


def test_unquoted_single_arg() -> None:
    assert normalize_args("echo hello") == ["echo", "hello"]


def test_single_quoted_arg() -> None:
    assert normalize_args("echo 'hello'") == ["echo", "hello"]


def test_single_quoted_arg_with_spaces() -> None:
    assert normalize_args("echo 'hello world'") == ["echo", "hello world"]


def test_single_quoted_arg_with_spaces_and_quotes() -> None:
    assert normalize_args("echo 'hello \"world\"'") == ["echo", 'hello "world"']


def test_command_with_quoted_subcommand() -> None:
    assert normalize_args("outer_shell", "-c", "inner_shell -c 'command two'") == [
        "outer_shell",
        "-c",
        "inner_shell -c 'command two'",
    ]


def test_unquoted_subcommand_in_sequence() -> None:
    args = [
        "outer_shell",
        "inner_shell",
        "-c",
        "command two",
    ]
    normalized = normalize_args(*args)
    assert normalized == [
        "outer_shell",
        "inner_shell",
        "-c",
        "command two",
    ]
    joined = join_normalized_args(normalized)
    assert joined == "outer_shell inner_shell -c 'command two'"
