import json
from pathlib import Path
from lib.io import append_jsonl, atomic_write, atomic_write_bytes, log, utc_now


def test_utc_now_is_iso_string():
    result = utc_now()
    assert isinstance(result, str)
    assert "T" in result
    assert "+00:00" in result or result.endswith("Z")


def test_log_prints(capsys):
    log("hello test")
    captured = capsys.readouterr()
    assert "hello test" in captured.out


def test_atomic_write_creates_file(tmp_path):
    p = tmp_path / "out.txt"
    atomic_write(p, "content")
    assert p.exists()
    assert p.read_text() == "content"


def test_atomic_write_creates_parent_dirs(tmp_path):
    p = tmp_path / "a" / "b" / "out.txt"
    atomic_write(p, "nested")
    assert p.read_text() == "nested"


def test_atomic_write_overwrites_existing(tmp_path):
    p = tmp_path / "out.txt"
    p.write_text("old")
    atomic_write(p, "new")
    assert p.read_text() == "new"


def test_atomic_write_bytes_creates_file(tmp_path):
    p = tmp_path / "img.bin"
    atomic_write_bytes(p, b"\x00\x01\x02")
    assert p.read_bytes() == b"\x00\x01\x02"


def test_atomic_write_bytes_creates_parent_dirs(tmp_path):
    p = tmp_path / "sub" / "img.bin"
    atomic_write_bytes(p, b"data")
    assert p.read_bytes() == b"data"


def test_append_jsonl_creates_file(tmp_path):
    p = tmp_path / "records.jsonl"
    append_jsonl(p, {"a": 1})
    lines = p.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"a": 1}


def test_append_jsonl_appends_multiple(tmp_path):
    p = tmp_path / "records.jsonl"
    append_jsonl(p, {"n": 1})
    append_jsonl(p, {"n": 2})
    lines = p.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["n"] == 1
    assert json.loads(lines[1])["n"] == 2


def test_append_jsonl_creates_parent_dirs(tmp_path):
    p = tmp_path / "sub" / "records.jsonl"
    append_jsonl(p, {"x": "y"})
    assert p.exists()
