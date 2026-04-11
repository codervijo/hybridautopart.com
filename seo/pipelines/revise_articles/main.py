#!/usr/bin/env python3
"""
SEO Article Reviser
Applies the '🔁 Improved Sections' rewrites from review_articles output back
into the original articles produced by write_articles.

Input:
  INPUT_ARTICLES_DIR/  — original .md files (write_articles output)
  INPUT_REVIEWS_DIR/   — review .md files (review_articles output, same slug)

Output:
  output/<slug>.md     — revised article with improvements applied
"""

import json
import os
import re
import sys
import time
import random
import tempfile
import shutil
import datetime
import urllib.request
import urllib.error
from pathlib import Path
from string import Template

import sys as _sys
_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_SEO_ROOT))
from lib.prompts import load_prompt as _lp, prompt_hash as _prompt_hash

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    return _lp(name, PROMPTS_DIR)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_env_file(path: str = "revise.env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_config() -> dict:
    load_env_file()
    return {
        "input_articles_dir": Path(os.environ.get("INPUT_ARTICLES_DIR", "input/articles")),
        "input_reviews_dir":  Path(os.environ.get("INPUT_REVIEWS_DIR",  "input/reviews")),
        "output_dir":         Path(os.environ.get("OUTPUT_DIR", "output")),
        "api_key":            os.environ.get("API_KEY", ""),
        "model":              os.environ.get("MODEL", "gpt-4.1-mini"),
        "api_url":            os.environ.get("API_URL", "https://api.openai.com/v1/chat/completions"),
        "delay_ms":           int(os.environ.get("DELAY_MS", "2000")),
        "jitter_ms":          int(os.environ.get("JITTER_MS", "1000")),
        "max_tokens":         int(os.environ.get("MAX_TOKENS", "8192")),
        "max_retries":        int(os.environ.get("MAX_RETRIES", "3")),
        "timeout":            int(os.environ.get("TIMEOUT", "120")),
        "max_consecutive_failures": int(os.environ.get("MAX_CONSECUTIVE_FAILURES", "5")),
        "continue_on_error":  os.environ.get("CONTINUE_ON_ERROR", "true").lower() == "true",
    }


# ---------------------------------------------------------------------------
# Input: pair articles with their reviews
# ---------------------------------------------------------------------------

def discover_pairs(articles_dir: Path, reviews_dir: Path) -> list[dict]:
    """
    Return one dict per article that has a matching review.
    Articles without a review are skipped with a warning.
    """
    if not articles_dir.exists():
        log(f"ERROR [FILE_NOT_FOUND]: Articles directory not found: {articles_dir}")
        sys.exit(1)
    if not reviews_dir.exists():
        log(f"ERROR [FILE_NOT_FOUND]: Reviews directory not found: {reviews_dir}")
        sys.exit(1)

    article_files = sorted(articles_dir.glob("*.md"))
    if not article_files:
        log(f"WARNING: No .md files found in {articles_dir}")
        return []

    pairs = []
    for article_path in article_files:
        slug = article_path.stem
        review_path = reviews_dir / f"{slug}.md"
        if not review_path.exists():
            log(f"SKIP [NO_REVIEW]: {slug} — no matching review in {reviews_dir}")
            continue
        pairs.append({
            "slug":            slug,
            "article_path":    article_path,
            "review_path":     review_path,
            "article_content": article_path.read_text(encoding="utf-8"),
            "review_content":  review_path.read_text(encoding="utf-8"),
        })

    return pairs


# ---------------------------------------------------------------------------
# AI revision
# ---------------------------------------------------------------------------

def revise_ai(pair: dict, config: dict) -> str:
    """Call an OpenAI-compatible chat completions endpoint to apply the review."""
    user_prompt = Template(load_prompt("user")).substitute(
        original_article=pair["article_content"],
        review=pair["review_content"],
    )

    payload = json.dumps({
        "model":      config["model"],
        "messages": [
            {"role": "system", "content": load_prompt("system")},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens":  config["max_tokens"],
    }).encode()

    req = urllib.request.Request(
        config["api_url"],
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=config["timeout"]) as resp:
        result = json.loads(resp.read().decode())

    return result["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------

def with_retry(fn, max_retries: int, label: str):
    attempt = 0
    last_error = None
    while attempt <= max_retries:
        try:
            return fn()
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code in (401, 403):
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"RETRY [{attempt + 1}/{max_retries}] {label} — HTTP {e.code}, waiting {wait:.1f}s")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_error = e
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"RETRY [{attempt + 1}/{max_retries}] {label} — {e}, waiting {wait:.1f}s")
        except Exception as e:
            last_error = e
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"RETRY [{attempt + 1}/{max_retries}] {label} — {type(e).__name__}: {e}, waiting {wait:.1f}s")
        attempt += 1
        if attempt <= max_retries:
            time.sleep(wait)
    raise last_error


# ---------------------------------------------------------------------------
# Atomic file I/O
# ---------------------------------------------------------------------------

def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8",
        dir=path.parent, suffix=".tmp", delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    shutil.move(tmp_path, path)
    os.chmod(path, 0o666)


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
    os.chmod(path, 0o666)


# ---------------------------------------------------------------------------
# Run state
# ---------------------------------------------------------------------------

class RunState:
    def __init__(self, output_dir: Path):
        self.state_dir      = output_dir / "run_state"
        self.status_path    = self.state_dir / "status.jsonl"
        self.failures_path  = self.state_dir / "failures.jsonl"
        self.summary_path   = self.state_dir / "summary.json"
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

    def record_success(self, slug: str, output_path: Path, phash: str = "") -> None:
        record = {
            "slug":        slug,
            "output_path": str(output_path),
            "prompt_hash": phash,
            "timestamp":   _now(),
        }
        append_jsonl(self.status_path, record)
        self._completed.add(slug)

    def record_failure(self, slug: str, error: Exception, retry_count: int, error_code: str = "ERR") -> None:
        record = {
            "slug":        slug,
            "error_code":  error_code,
            "message":     str(error),
            "retry_count": retry_count,
            "timestamp":   _now(),
        }
        append_jsonl(self.failures_path, record)

    def write_summary(self, total: int, success: int, failed: int, skipped: int) -> None:
        summary = {
            "total":     total,
            "success":   success,
            "failed":    failed,
            "skipped":   skipped,
            "timestamp": _now(),
        }
        atomic_write(self.summary_path, json.dumps(summary, indent=2, ensure_ascii=False))


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


# ---------------------------------------------------------------------------
# Logging / error codes
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def error_code_for(e: Exception) -> str:
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP_{e.code}"
    if isinstance(e, urllib.error.URLError):
        return "URL_ERROR"
    if isinstance(e, TimeoutError):
        return "TIMEOUT"
    if isinstance(e, FileNotFoundError):
        return "FILE_NOT_FOUND"
    return "ERR"


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run() -> None:
    config = get_config()
    output_dir = config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    if not config["api_key"] or config["api_key"] == "your_key_here":
        log("ERROR [CONFIG]: API_KEY is not set in revise.env")
        sys.exit(1)

    phash = _prompt_hash(PROMPTS_DIR / "system.txt", PROMPTS_DIR / "user.txt")

    pairs = discover_pairs(config["input_articles_dir"], config["input_reviews_dir"])
    log(f"Found {len(pairs)} article/review pair(s)")

    if not pairs:
        log("Nothing to do.")
        return

    state = RunState(output_dir)

    total     = len(pairs)
    success_count    = 0
    failed_count     = 0
    skipped_count    = 0
    consecutive_failures = 0

    for pair in pairs:
        slug = pair["slug"]

        if state.is_done(slug):
            log(f"SKIP: {slug} (already revised)")
            skipped_count += 1
            continue

        log(f"START: {slug}")

        try:
            revised = with_retry(
                lambda p=pair: revise_ai(p, config),
                max_retries=config["max_retries"],
                label=slug,
            )
        except Exception as e:
            code = error_code_for(e)
            log(f"ERROR [{code}]: {slug} — {e}")
            state.record_failure(slug, e, config["max_retries"], code)
            failed_count += 1
            consecutive_failures += 1
            if consecutive_failures >= config["max_consecutive_failures"]:
                log(f"ERROR [MAX_FAILURES]: {consecutive_failures} consecutive failures. Stopping.")
                break
            if not config["continue_on_error"]:
                log("ERROR [ABORT]: continue_on_error=false. Stopping.")
                break
            continue

        out_path = output_dir / f"{slug}.md"
        try:
            atomic_write(out_path, revised)
        except Exception as e:
            log(f"ERROR [WRITE_ERROR]: Could not write {out_path} — {e}")
            state.record_failure(slug, e, 0, "WRITE_ERROR")
            failed_count += 1
            consecutive_failures += 1
            if not config["continue_on_error"]:
                break
            continue

        state.record_success(slug, out_path, phash)
        success_count += 1
        consecutive_failures = 0
        log(f"SUCCESS: {slug}")

        delay_s = config["delay_ms"] / 1000.0
        jitter_s = random.uniform(0, config["jitter_ms"] / 1000.0)
        total_delay = delay_s + jitter_s
        if total_delay > 0:
            log(f"  sleeping {total_delay:.1f}s...")
            time.sleep(total_delay)

    state.write_summary(
        total=total,
        success=success_count,
        failed=failed_count,
        skipped=skipped_count,
    )
    log(
        f"\nDone. total={total} success={success_count} "
        f"failed={failed_count} skipped={skipped_count}"
    )


if __name__ == "__main__":
    run()
