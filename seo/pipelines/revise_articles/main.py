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
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from string import Template

_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.env import load_env_file
from lib.http import error_code_for, with_retry
from lib.io import atomic_write, log
from lib.prompts import LIB_DIR as _LIB_DIR, load_prompt as _lp, load_system_prompt, prompt_hash as _prompt_hash, validate_template_vars
from lib.run_state import RunState

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    return _lp(name, PROMPTS_DIR)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def get_config() -> dict:
    load_env_file("revise.env")
    return {
        "input_articles_dir":      Path(os.environ.get("INPUT_ARTICLES_DIR", "input/articles")),
        "input_reviews_dir":       Path(os.environ.get("INPUT_REVIEWS_DIR",  "input/reviews")),
        "output_dir":              Path(os.environ.get("OUTPUT_DIR", "output")),
        "api_key":                 os.environ.get("API_KEY", ""),
        "model":                   os.environ.get("MODEL", "gpt-4.1-mini"),
        "api_url":                 os.environ.get("API_URL", "https://api.openai.com/v1/chat/completions"),
        "delay_ms":                int(os.environ.get("DELAY_MS", "2000")),
        "jitter_ms":               int(os.environ.get("JITTER_MS", "1000")),
        "max_tokens":              int(os.environ.get("MAX_TOKENS", "8192")),
        "max_retries":             int(os.environ.get("MAX_RETRIES", "3")),
        "timeout":                 int(os.environ.get("TIMEOUT", "120")),
        "max_consecutive_failures": int(os.environ.get("MAX_CONSECUTIVE_FAILURES", "5")),
        "continue_on_error":       os.environ.get("CONTINUE_ON_ERROR", "true").lower() == "true",
    }


# ---------------------------------------------------------------------------
# Input: pair articles with their reviews
# ---------------------------------------------------------------------------

def discover_pairs(articles_dir: Path, reviews_dir: Path) -> list[dict]:
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
        slug        = article_path.stem
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
    tmpl  = load_prompt("user")
    vars_ = dict(
        original_article=pair["article_content"],
        review=pair["review_content"],
    )
    validate_template_vars(tmpl, vars_, label="revise_articles/user.txt")
    user_prompt = Template(tmpl).substitute(vars_)

    payload = json.dumps({
        "model":    config["model"],
        "messages": [
            {"role": "system", "content": load_system_prompt(PROMPTS_DIR)},
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
# Main runner
# ---------------------------------------------------------------------------

def run() -> None:
    config = get_config()

    if not config["api_key"] or config["api_key"] == "your_key_here":
        log("ERROR [CONFIG]: API_KEY is not set in revise.env")
        sys.exit(1)

    output_dir = config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    phash = _prompt_hash(_LIB_DIR / "persona.txt", PROMPTS_DIR / "system.txt", PROMPTS_DIR / "user.txt")
    pairs = discover_pairs(config["input_articles_dir"], config["input_reviews_dir"])
    log(f"Found {len(pairs)} article/review pair(s)")

    if not pairs:
        log("Nothing to do.")
        return

    state = RunState(output_dir)

    total             = len(pairs)
    success_count     = 0
    failed_count      = 0
    skipped_count     = 0
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
        if (total_delay := delay_s + jitter_s) > 0:
            log(f"  sleeping {total_delay:.1f}s...")
            time.sleep(total_delay)

    state.write_summary(total=total, success=success_count,
                        failed=failed_count, skipped=skipped_count)
    log(f"\nDone. total={total} success={success_count} "
        f"failed={failed_count} skipped={skipped_count}")


if __name__ == "__main__":
    run()
