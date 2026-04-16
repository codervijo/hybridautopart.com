#!/usr/bin/env python3
"""
SEO Blog Post Generator — OpenAI-compatible API.
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
from lib.prompts import load_prompt as _lp, prompt_hash as _prompt_hash, validate_template_vars, load_system_prompt, LIB_DIR as _LIB_DIR

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    return _lp(name, PROMPTS_DIR)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_env_file(path="blogs.env"):
    """Parse a .env file and set values in os.environ (file < system env)."""
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


def get_config():
    load_env_file()
    return {
        "input_json": os.environ.get("INPUT_JSON", "input/topics.json"),
        "output_dir": Path(os.environ.get("OUTPUT_DIR", "output")),
        "api_key": os.environ.get("API_KEY", ""),
        "model": os.environ.get("MODEL", "gpt-4.1-mini"),
        "api_url": os.environ.get("API_URL", "https://api.openai.com/v1/chat/completions"),
        "delay_ms": int(os.environ.get("DELAY_MS", "2000")),
        "jitter_ms": int(os.environ.get("JITTER_MS", "1000")),
        "max_tokens": int(os.environ.get("MAX_TOKENS", "8192")),
        "extra_ms_per_1k_words": int(os.environ.get("EXTRA_MS_PER_1K_WORDS", "3000")),
        "max_retries": int(os.environ.get("MAX_RETRIES", "3")),
        "timeout": int(os.environ.get("TIMEOUT", "60")),
        "max_consecutive_failures": int(os.environ.get("MAX_CONSECUTIVE_FAILURES", "5")),
        "continue_on_error": os.environ.get("CONTINUE_ON_ERROR", "true").lower() == "true",
    }


# ---------------------------------------------------------------------------
# Input parsing & normalization
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def keyword_to_title(keyword: str) -> str:
    """Format a keyword into a readable title."""
    stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at",
                  "to", "for", "of", "with", "by", "from", "is", "are"}
    words = keyword.strip().split()
    titled = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in stop_words:
            titled.append(word.capitalize())
        else:
            titled.append(word.lower())
    return " ".join(titled)


def normalize_topic(raw: dict, index: int) -> dict:
    """Normalize a raw topic dict into a standard structure."""
    # Support Format A: {"keyword": "..."}
    keyword = (
        raw.get("primary_keyword")
        or raw.get("keyword")
        or raw.get("title", "")
    ).strip()

    title = (raw.get("title") or keyword_to_title(keyword)).strip()

    slug = raw.get("slug") or slugify(title) or slugify(keyword) or f"post-{index + 1}"

    return {
        "id": raw.get("id", index + 1),
        "title": title,
        "keyword": keyword,
        "slug": slug,
        "cluster": raw.get("cluster", ""),
        "search_intent": raw.get("search_intent", "Informational"),
        "priority": raw.get("priority", "Medium"),
        "target_word_count": int(raw.get("target_word_count", 1200)),
        "aeo_snippet_target": bool(raw.get("aeo_snippet_target", False)),
        "suggested_internal_links": raw.get("suggested_internal_links") or [],
    }


def parse_input(path: str) -> list[dict]:
    """Load and parse the input JSON, auto-detecting format."""
    with open(path) as f:
        data = json.load(f)

    # Format A: list of {"keyword": "..."}
    if isinstance(data, list):
        raw_topics = data
    # Format B: {"posts": [...]}
    elif isinstance(data, dict) and "posts" in data:
        raw_topics = data["posts"]
    else:
        raise ValueError(f"Unrecognized input format in {path}")

    return [normalize_topic(raw, i) for i, raw in enumerate(raw_topics)]


# ---------------------------------------------------------------------------
# Content generation — AI mode
# ---------------------------------------------------------------------------

def _build_prompt(topic: dict) -> str:
    links = topic["suggested_internal_links"]
    aeo = topic["aeo_snippet_target"]

    link_instruction = ""
    if links:
        link_list = ", ".join(f"`/{l}/`" for l in links)
        link_instruction = (
            f"\n- Naturally incorporate these internal links (as markdown links): {link_list}"
        )

    aeo_instruction = (
        "- Begin with a **Quick Answer** section (40–60 words) that directly answers the query — "
        "this targets Google's featured snippet.\n"
        if aeo
        else ""
    )

    tmpl = load_prompt("user")
    vars_ = dict(
        title=topic["title"],
        keyword=topic["keyword"],
        intent=topic["search_intent"],
        target_word_count=topic["target_word_count"],
        aeo_instruction=aeo_instruction,
        link_instruction=link_instruction,
    )
    validate_template_vars(tmpl, vars_, label="write_articles/user.txt")
    return Template(tmpl).substitute(vars_)


def generate_ai(topic: dict, config: dict) -> str:
    """Call an OpenAI-compatible chat completions endpoint."""
    import json as _json

    payload = _json.dumps({
        "model": config["model"],
        "messages": [
            {"role": "system", "content": load_system_prompt(PROMPTS_DIR)},
            {"role": "user", "content": _build_prompt(topic)},
        ],
        "temperature": 0.7,
        "max_tokens": config["max_tokens"],
    }).encode()

    req = urllib.request.Request(
        config["api_url"],
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=config["timeout"]) as resp:
        result = _json.loads(resp.read().decode())

    return result["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------

def with_retry(fn, max_retries: int, label: str):
    """Call fn(), retrying with exponential backoff on failure."""
    attempt = 0
    last_error = None
    while attempt <= max_retries:
        if attempt > 0:
            log(f"  attempt {attempt + 1} of {max_retries + 1}...")
        try:
            return fn()
        except urllib.error.HTTPError as e:
            last_error = e
            code = e.code
            if code in (401, 403):
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"  ERROR: HTTP {code} — {e.reason}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_error = e
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"  ERROR: {type(e).__name__}: {e}")
        except Exception as e:
            last_error = e
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"  ERROR: {type(e).__name__}: {e}")

        attempt += 1
        if attempt <= max_retries:
            log(f"  retrying in {wait:.1f}s (attempt {attempt + 1} of {max_retries + 1})...")
            time.sleep(wait)
        else:
            log(f"  all {max_retries + 1} attempts failed for: {label}")

    raise last_error


# ---------------------------------------------------------------------------
# Atomic file I/O
# ---------------------------------------------------------------------------

def atomic_write(path: Path, content: str):
    """Write content to path atomically via a temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8",
        dir=path.parent, suffix=".tmp", delete=False
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    shutil.move(tmp_path, path)
    os.chmod(path, 0o666)


def append_jsonl(path: Path, record: dict):
    """Append a JSON record as a line to a .jsonl file (atomic per-line)."""
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
        self.state_dir = output_dir / "run_state"
        self.status_path = self.state_dir / "status.jsonl"
        self.failures_path = self.state_dir / "failures.jsonl"
        self.summary_path = self.state_dir / "summary.json"
        self._completed_slugs: set[str] = set()
        self._load_completed()

    def _load_completed(self):
        if self.status_path.exists():
            with open(self.status_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if rec.get("slug"):
                            self._completed_slugs.add(rec["slug"])
                    except json.JSONDecodeError:
                        pass

    def is_done(self, slug: str) -> bool:
        return slug in self._completed_slugs

    def record_success(self, topic: dict, output_path: Path, mode: str, phash: str = ""):
        record = {
            "id": topic.get("id"),
            "keyword": topic["keyword"],
            "title": topic["title"],
            "slug": topic["slug"],
            "output_path": str(output_path),
            "mode": mode,
            "prompt_hash": phash,
            "timestamp": _now(),
        }
        append_jsonl(self.status_path, record)
        self._completed_slugs.add(topic["slug"])

    def record_failure(self, topic: dict, error: Exception, retry_count: int, error_code: str = "ERR"):
        record = {
            "id": topic.get("id"),
            "keyword": topic["keyword"],
            "title": topic["title"],
            "slug": topic["slug"],
            "error_code": error_code,
            "message": str(error),
            "retry_count": retry_count,
            "timestamp": _now(),
        }
        append_jsonl(self.failures_path, record)

    def write_summary(self, total: int, success: int, failed: int, skipped: int, mode: str):
        summary = {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "mode": mode,
            "timestamp": _now(),
        }
        atomic_write(self.summary_path, json.dumps(summary, indent=2, ensure_ascii=False))


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

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


def run():
    config = get_config()

    if not config["api_key"]:
        log("ERROR [NO_API_KEY]: API_KEY is not set.")
        log("  Set it in blogs.env:  API_KEY=your-key-here")
        log("  or export it:         export API_KEY=your-key-here")
        sys.exit(1)

    output_dir: Path = config["output_dir"]
    posts_dir = output_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    phash = _prompt_hash(_LIB_DIR / "persona.txt", PROMPTS_DIR / "system.txt", PROMPTS_DIR / "user.txt")

    # Load topics
    input_path = config["input_json"]
    if not Path(input_path).exists():
        log(f"ERROR [FILE_NOT_FOUND]: Input file not found: {input_path}")
        sys.exit(1)

    try:
        topics = parse_input(input_path)
    except Exception as e:
        log(f"ERROR [PARSE_ERROR]: Failed to parse input: {e}")
        sys.exit(1)

    log(f"Loaded {len(topics)} topic(s) from {input_path}")
    log(f"Model: {config['model']}  API: {config['api_url']}")
    log(f"Max retries: {config['max_retries']}  Max tokens: {config['max_tokens']}")
    log("")

    state = RunState(output_dir)

    total = len(topics)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    consecutive_failures = 0

    for i, topic in enumerate(topics):
        slug = topic["slug"]
        keyword = topic["keyword"]

        # Resume: skip already completed
        if state.is_done(slug):
            log(f"[{i+1}/{total}] SKIP {slug} (already completed)")
            skipped_count += 1
            continue

        log(f"[{i+1}/{total}] Generating: {keyword} ({topic['target_word_count']} words)...")

        def generate():
            return generate_ai(topic, config)

        try:
            content = with_retry(
                generate,
                max_retries=config["max_retries"],
                label=slug,
            )
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                log(f"  ERROR: HTTP {e.code} — API key rejected.")
                log("  This usually means the key is invalid, expired, or revoked.")
                log("  Get or rotate your key at: https://platform.openai.com/api-keys")
                log("  Then update API_KEY in blogs.env or your environment.")
                sys.exit(1)
            code = error_code_for(e)
            log(f"  FAILED [{code}]: {slug}")
            state.record_failure(topic, e, config["max_retries"], code)
            failed_count += 1
            consecutive_failures += 1
        except Exception as e:
            code = error_code_for(e)
            log(f"  FAILED [{code}]: {slug}")
            state.record_failure(topic, e, config["max_retries"], code)
            failed_count += 1
            consecutive_failures += 1
        else:
            # Write post file atomically
            out_path = posts_dir / f"{slug}.md"
            try:
                atomic_write(out_path, content)
            except Exception as e:
                log(f"  ERROR [WRITE_ERROR]: Could not write {out_path} — {e}")
                state.record_failure(topic, e, 0, "WRITE_ERROR")
                failed_count += 1
                consecutive_failures += 1
                if not config["continue_on_error"]:
                    log("  Stopping (continue_on_error=false).")
                    break
                continue

            state.record_success(topic, out_path, "ai", phash)
            success_count += 1
            consecutive_failures = 0
            log(f"  OK -> {out_path}")

            # Delay between posts — extra time proportional to word count to
            # avoid hitting TPM limits on longer articles.
            delay_s = config["delay_ms"] / 1000.0
            jitter_s = random.uniform(0, config["jitter_ms"] / 1000.0)
            wc_extra_s = topic["target_word_count"] / 1000.0 * config["extra_ms_per_1k_words"] / 1000.0
            total_delay = delay_s + jitter_s + wc_extra_s
            if total_delay > 0:
                log(f"  sleeping {total_delay:.1f}s...")
                time.sleep(total_delay)
            continue

        if consecutive_failures >= config["max_consecutive_failures"]:
            log(f"ERROR [MAX_FAILURES]: {consecutive_failures} consecutive failures. Stopping.")
            break

        if not config["continue_on_error"]:
            log("  Stopping (continue_on_error=false).")
            break

    log("")
    state.write_summary(
        total=total,
        success=success_count,
        failed=failed_count,
        skipped=skipped_count,
        mode="ai",
    )

    log(
        f"Done. total={total} success={success_count} "
        f"failed={failed_count} skipped={skipped_count}"
    )


if __name__ == "__main__":
    run()
