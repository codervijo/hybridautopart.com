import json
from pathlib import Path

from lib.io import append_jsonl, atomic_write, utc_now


class RunState:
    def __init__(self, output_dir: Path) -> None:
        self.state_dir     = output_dir / "run_state"
        self.status_path   = self.state_dir / "status.jsonl"
        self.failures_path = self.state_dir / "failures.jsonl"
        self.summary_path  = self.state_dir / "summary.json"
        self._completed: set[str] = set()
        self._load_completed()

    def _load_completed(self) -> None:
        if not self.status_path.exists():
            return
        with open(self.status_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("slug"):
                        self._completed.add(rec["slug"])
                except json.JSONDecodeError:
                    pass

    def is_done(self, slug: str) -> bool:
        return slug in self._completed

    def record_success(self, slug: str, output_path: Path, phash: str = "", **extra) -> None:
        record = {
            "slug":        slug,
            "output_path": str(output_path),
            "prompt_hash": phash,
            "timestamp":   utc_now(),
            **extra,
        }
        append_jsonl(self.status_path, record)
        self._completed.add(slug)

    def record_failure(self, slug: str, error: Exception, retry_count: int, error_code: str = "ERR", **extra) -> None:
        record = {
            "slug":        slug,
            "error_code":  error_code,
            "message":     str(error),
            "retry_count": retry_count,
            "timestamp":   utc_now(),
            **extra,
        }
        append_jsonl(self.failures_path, record)

    def write_summary(self, total: int, success: int, failed: int, skipped: int, **extra) -> None:
        summary = {
            "total":     total,
            "success":   success,
            "failed":    failed,
            "skipped":   skipped,
            "timestamp": utc_now(),
            **extra,
        }
        atomic_write(self.summary_path, json.dumps(summary, indent=2, ensure_ascii=False))
