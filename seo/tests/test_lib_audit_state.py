import datetime
import json

from lib.audit_state import (
    list_dated,
    read_latest,
    read_previous,
    stage_path,
    today_str,
    write_dated,
)


def test_today_str_format():
    s = today_str()
    datetime.datetime.strptime(s, "%Y-%m-%d")  # raises if not YYYY-MM-DD


def test_stage_path_layout(tmp_path):
    p = stage_path(tmp_path, "crawls", "2026-04-26")
    assert p == tmp_path / "crawls" / "2026-04-26.json"


def test_write_dated_creates_dated_and_latest(tmp_path):
    out = write_dated(tmp_path, "crawls", {"pages": [1, 2]}, date="2026-04-26")
    assert out == tmp_path / "crawls" / "2026-04-26.json"
    assert json.loads(out.read_text())["pages"] == [1, 2]
    latest = tmp_path / "crawls" / "latest.json"
    assert latest.exists()
    assert json.loads(latest.read_text())["pages"] == [1, 2]


def test_write_dated_uses_today_when_date_missing(tmp_path):
    write_dated(tmp_path, "audits/technical", {"x": 1})
    today = today_str()
    assert (tmp_path / "audits" / "technical" / f"{today}.json").exists()


def test_write_dated_overwrites_same_day(tmp_path):
    write_dated(tmp_path, "crawls", {"v": 1}, date="2026-04-26")
    write_dated(tmp_path, "crawls", {"v": 2}, date="2026-04-26")
    p = tmp_path / "crawls" / "2026-04-26.json"
    assert json.loads(p.read_text())["v"] == 2
    assert json.loads((tmp_path / "crawls" / "latest.json").read_text())["v"] == 2


def test_read_latest_missing_returns_none(tmp_path):
    assert read_latest(tmp_path, "crawls") is None


def test_read_latest_returns_payload(tmp_path):
    write_dated(tmp_path, "crawls", {"a": "b"}, date="2026-04-26")
    assert read_latest(tmp_path, "crawls") == {"a": "b"}


def test_list_dated_excludes_latest_and_garbage(tmp_path):
    stage = tmp_path / "crawls"
    stage.mkdir()
    (stage / "2026-04-25.json").write_text("{}")
    (stage / "2026-04-26.json").write_text("{}")
    (stage / "latest.json").write_text("{}")
    (stage / "notes.json").write_text("{}")
    assert list_dated(tmp_path, "crawls") == ["2026-04-25", "2026-04-26"]


def test_list_dated_missing_stage_returns_empty(tmp_path):
    assert list_dated(tmp_path, "nope") == []


def test_read_previous_returns_most_recent_earlier(tmp_path):
    write_dated(tmp_path, "crawls", {"d": "20"}, date="2026-04-20")
    write_dated(tmp_path, "crawls", {"d": "23"}, date="2026-04-23")
    write_dated(tmp_path, "crawls", {"d": "26"}, date="2026-04-26")
    assert read_previous(tmp_path, "crawls", before="2026-04-26")["d"] == "23"


def test_read_previous_none_when_no_earlier(tmp_path):
    write_dated(tmp_path, "crawls", {"d": "26"}, date="2026-04-26")
    assert read_previous(tmp_path, "crawls", before="2026-04-26") is None
