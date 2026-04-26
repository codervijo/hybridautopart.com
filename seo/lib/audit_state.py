import datetime
import json
from pathlib import Path

from lib.io import atomic_write


def today_str() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def stage_path(data_root: Path, stage: str, date: str) -> Path:
    return data_root / stage / f"{date}.json"


def write_dated(data_root: Path, stage: str, payload: dict, date: str | None = None) -> Path:
    """Write payload to data/<stage>/YYYY-MM-DD.json and update latest.json pointer."""
    if date is None:
        date = today_str()
    out = stage_path(data_root, stage, date)
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    atomic_write(out, body)
    atomic_write(data_root / stage / "latest.json", body)
    return out


def read_latest(data_root: Path, stage: str) -> dict | None:
    """Return latest.json content for a stage, or None if not yet written."""
    latest = data_root / stage / "latest.json"
    if not latest.exists():
        return None
    return json.loads(latest.read_text(encoding="utf-8"))


def list_dated(data_root: Path, stage: str) -> list[str]:
    """Return sorted YYYY-MM-DD stems of dated stage files (excludes latest.json)."""
    stage_dir = data_root / stage
    if not stage_dir.exists():
        return []
    out: list[str] = []
    for f in stage_dir.glob("*.json"):
        if f.stem == "latest":
            continue
        try:
            datetime.datetime.strptime(f.stem, "%Y-%m-%d")
        except ValueError:
            continue
        out.append(f.stem)
    return sorted(out)


def read_previous(data_root: Path, stage: str, before: str | None = None) -> dict | None:
    """Return content of the most recent dated file strictly before `before` (default: today)."""
    if before is None:
        before = today_str()
    earlier = [d for d in list_dated(data_root, stage) if d < before]
    if not earlier:
        return None
    return json.loads(stage_path(data_root, stage, earlier[-1]).read_text(encoding="utf-8"))
