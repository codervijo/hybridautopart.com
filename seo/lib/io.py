import datetime
import json
import os
import shutil
import tempfile
from pathlib import Path


def log(msg: str) -> None:
    print(msg, flush=True)


def utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically via a temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8",
        dir=path.parent, suffix=".tmp", delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    shutil.move(tmp_path, path)
    os.chmod(path, 0o666)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write bytes to path atomically via a temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent, suffix=".tmp", delete=False,
    ) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    shutil.move(tmp_path, path)
    os.chmod(path, 0o666)


def append_jsonl(path: Path, record: dict) -> None:
    """Append a JSON record as a line to a .jsonl file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
    os.chmod(path, 0o666)
