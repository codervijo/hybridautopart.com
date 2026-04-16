import json
import pytest
from pathlib import Path
from lib.run_state import RunState


def test_is_done_false_for_new_slug(tmp_path):
    state = RunState(tmp_path)
    assert not state.is_done("my-slug")


def test_record_success_marks_done(tmp_path):
    state = RunState(tmp_path)
    state.record_success("my-slug", tmp_path / "out.md")
    assert state.is_done("my-slug")


def test_record_success_writes_jsonl(tmp_path):
    state = RunState(tmp_path)
    state.record_success("slug-a", tmp_path / "out.md", phash="abc123")
    lines = (tmp_path / "run_state" / "status.jsonl").read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["slug"] == "slug-a"
    assert record["prompt_hash"] == "abc123"
    assert "timestamp" in record
    assert "output_path" in record


def test_record_success_stores_extra_kwargs(tmp_path):
    state = RunState(tmp_path)
    state.record_success("s", tmp_path / "x", keyword="hybrid battery", mode="ai")
    record = json.loads(
        (tmp_path / "run_state" / "status.jsonl").read_text().splitlines()[0]
    )
    assert record["keyword"] == "hybrid battery"
    assert record["mode"] == "ai"


def test_record_failure_writes_failures_jsonl(tmp_path):
    state = RunState(tmp_path)
    state.record_failure("bad-slug", RuntimeError("boom"), retry_count=3, error_code="HTTP_500")
    lines = (tmp_path / "run_state" / "failures.jsonl").read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["slug"] == "bad-slug"
    assert record["error_code"] == "HTTP_500"
    assert record["message"] == "boom"
    assert record["retry_count"] == 3


def test_record_failure_does_not_mark_done(tmp_path):
    state = RunState(tmp_path)
    state.record_failure("bad-slug", RuntimeError("x"), retry_count=1)
    assert not state.is_done("bad-slug")


def test_write_summary_creates_json(tmp_path):
    state = RunState(tmp_path)
    state.write_summary(total=10, success=8, failed=1, skipped=1)
    summary = json.loads((tmp_path / "run_state" / "summary.json").read_text())
    assert summary["total"] == 10
    assert summary["success"] == 8
    assert summary["failed"] == 1
    assert summary["skipped"] == 1
    assert "timestamp" in summary


def test_write_summary_extra_kwargs(tmp_path):
    state = RunState(tmp_path)
    state.write_summary(total=1, success=1, failed=0, skipped=0, mode="ai")
    summary = json.loads((tmp_path / "run_state" / "summary.json").read_text())
    assert summary["mode"] == "ai"


def test_reload_picks_up_existing_status(tmp_path):
    # First run: complete some slugs
    state1 = RunState(tmp_path)
    state1.record_success("a", tmp_path / "a.md")
    state1.record_success("b", tmp_path / "b.md")

    # Second run: new RunState should recognise them as done
    state2 = RunState(tmp_path)
    assert state2.is_done("a")
    assert state2.is_done("b")
    assert not state2.is_done("c")


def test_multiple_successes_appended(tmp_path):
    state = RunState(tmp_path)
    state.record_success("a", tmp_path / "a.md")
    state.record_success("b", tmp_path / "b.md")
    lines = (tmp_path / "run_state" / "status.jsonl").read_text().splitlines()
    assert len(lines) == 2
