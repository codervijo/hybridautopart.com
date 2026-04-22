import os
import pytest
from lib.env import load_env_file


def test_missing_file_is_noop(tmp_path):
    load_env_file(str(tmp_path / "nonexistent.env"))  # must not raise


def test_sets_env_var(tmp_path, monkeypatch):
    env = tmp_path / "test.env"
    env.write_text("FOO=bar\n")
    monkeypatch.delenv("FOO", raising=False)
    load_env_file(str(env))
    assert os.environ["FOO"] == "bar"


def test_strips_double_quotes(tmp_path, monkeypatch):
    env = tmp_path / "test.env"
    env.write_text('FOO="hello world"\n')
    monkeypatch.delenv("FOO", raising=False)
    load_env_file(str(env))
    assert os.environ["FOO"] == "hello world"


def test_strips_single_quotes(tmp_path, monkeypatch):
    env = tmp_path / "test.env"
    env.write_text("FOO='hello world'\n")
    monkeypatch.delenv("FOO", raising=False)
    load_env_file(str(env))
    assert os.environ["FOO"] == "hello world"


def test_does_not_override_existing(tmp_path, monkeypatch):
    env = tmp_path / "test.env"
    env.write_text("FOO=from_file\n")
    monkeypatch.setenv("FOO", "from_env")
    load_env_file(str(env))
    assert os.environ["FOO"] == "from_env"


def test_skips_comments_and_blank_lines(tmp_path, monkeypatch):
    env = tmp_path / "test.env"
    env.write_text("# this is a comment\n\nFOO=set\n")
    monkeypatch.delenv("FOO", raising=False)
    load_env_file(str(env))
    assert os.environ["FOO"] == "set"


def test_skips_lines_without_equals(tmp_path, monkeypatch):
    env = tmp_path / "test.env"
    env.write_text("NOEQUALS\nGOOD=yes\n")
    monkeypatch.delenv("GOOD", raising=False)
    load_env_file(str(env))
    assert os.environ["GOOD"] == "yes"


def test_multiple_vars(tmp_path, monkeypatch):
    env = tmp_path / "test.env"
    env.write_text("A=1\nB=2\n")
    monkeypatch.delenv("A", raising=False)
    monkeypatch.delenv("B", raising=False)
    load_env_file(str(env))
    assert os.environ["A"] == "1"
    assert os.environ["B"] == "2"


def test_value_with_equals_sign(tmp_path, monkeypatch):
    env = tmp_path / "test.env"
    env.write_text("FOO=a=b\n")
    monkeypatch.delenv("FOO", raising=False)
    load_env_file(str(env))
    assert os.environ["FOO"] == "a=b"


# ---------------------------------------------------------------------------
# Cascade (multi-path) tests
# ---------------------------------------------------------------------------

def test_cascade_later_overrides_earlier(tmp_path, monkeypatch):
    base = tmp_path / "base.env"
    base.write_text("FOO=base\nBAR=base\n")
    override = tmp_path / "override.env"
    override.write_text("FOO=override\n")
    monkeypatch.delenv("FOO", raising=False)
    monkeypatch.delenv("BAR", raising=False)
    load_env_file(str(base), str(override))
    assert os.environ["FOO"] == "override"
    assert os.environ["BAR"] == "base"


def test_cascade_missing_first_path_is_noop(tmp_path, monkeypatch):
    second = tmp_path / "second.env"
    second.write_text("FOO=second\n")
    monkeypatch.delenv("FOO", raising=False)
    load_env_file(str(tmp_path / "nonexistent.env"), str(second))
    assert os.environ["FOO"] == "second"


def test_cascade_system_env_wins_over_all_files(tmp_path, monkeypatch):
    base = tmp_path / "base.env"
    base.write_text("FOO=base\n")
    override = tmp_path / "override.env"
    override.write_text("FOO=override\n")
    monkeypatch.setenv("FOO", "system")
    load_env_file(str(base), str(override))
    assert os.environ["FOO"] == "system"
