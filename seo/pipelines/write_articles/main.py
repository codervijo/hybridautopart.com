#!/usr/bin/env python3
"""
SEO Blog Post Generator — OpenAI-compatible API.
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
from lib.text import keyword_to_title, slugify

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    return _lp(name, PROMPTS_DIR)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def get_config() -> dict:
    load_env_file("../../seo.env", "blogs.env")
    return {
        "input_json":              os.environ.get("INPUT_JSON", "input/topics.json"),
        "output_dir":              Path(os.environ.get("OUTPUT_DIR", "output")),
        "api_key":                 os.environ.get("API_KEY", ""),
        "model":                   os.environ.get("MODEL", "gpt-4.1-mini"),
        "api_url":                 os.environ.get("API_URL", "https://api.openai.com/v1/chat/completions"),
        "delay_ms":                int(os.environ.get("DELAY_MS", "2000")),
        "jitter_ms":               int(os.environ.get("JITTER_MS", "1000")),
        "max_tokens":              int(os.environ.get("MAX_TOKENS", "8192")),
        "extra_ms_per_1k_words":   int(os.environ.get("EXTRA_MS_PER_1K_WORDS", "3000")),
        "max_retries":             int(os.environ.get("MAX_RETRIES", "3")),
        "timeout":                 int(os.environ.get("TIMEOUT", "60")),
        "max_consecutive_failures": int(os.environ.get("MAX_CONSECUTIVE_FAILURES", "5")),
        "continue_on_error":       os.environ.get("CONTINUE_ON_ERROR", "true").lower() == "true",
    }


# ---------------------------------------------------------------------------
# Input parsing & normalization
# ---------------------------------------------------------------------------

def normalize_topic(raw: dict, index: int) -> dict:
    keyword = (
        raw.get("primary_keyword")
        or raw.get("keyword")
        or raw.get("title", "")
    ).strip()

    title = (raw.get("title") or keyword_to_title(keyword)).strip()
    slug  = raw.get("slug") or slugify(title) or slugify(keyword) or f"post-{index + 1}"

    return {
        "id":                       raw.get("id", index + 1),
        "title":                    title,
        "keyword":                  keyword,
        "slug":                     slug,
        "cluster":                  raw.get("cluster", ""),
        "search_intent":            raw.get("search_intent", "Informational"),
        "priority":                 raw.get("priority", "Medium"),
        "target_word_count":        int(raw.get("target_word_count", 1200)),
        "aeo_snippet_target":       bool(raw.get("aeo_snippet_target", False)),
        "suggested_internal_links": raw.get("suggested_internal_links") or [],
    }


def parse_input(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)

    if isinstance(data, list):
        raw_topics = data
    elif isinstance(data, dict) and "posts" in data:
        raw_topics = data["posts"]
    else:
        raise ValueError(f"Unrecognized input format in {path}")

    return [normalize_topic(raw, i) for i, raw in enumerate(raw_topics)]


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------

def _build_prompt(topic: dict) -> str:
    links = topic["suggested_internal_links"]
    aeo   = topic["aeo_snippet_target"]

    link_instruction = ""
    if links:
        link_list = ", ".join(f"`/{l}/`" for l in links)
        link_instruction = (
            f"\n- Naturally incorporate these internal links (as markdown links): {link_list}"
        )

    aeo_instruction = (
        "- Begin with a **Quick Answer** section (40–60 words) that directly answers the query — "
        "this targets Google's featured snippet.\n"
        if aeo else ""
    )

    tmpl  = load_prompt("user")
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
    payload = json.dumps({
        "model":    config["model"],
        "messages": [
            {"role": "system", "content": load_system_prompt(PROMPTS_DIR)},
            {"role": "user",   "content": _build_prompt(topic)},
        ],
        "temperature": 0.7,
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

    if not config["api_key"]:
        log("ERROR [NO_API_KEY]: API_KEY is not set.")
        log("  Set it in blogs.env:  API_KEY=your-key-here")
        log("  or export it:         export API_KEY=your-key-here")
        sys.exit(1)

    output_dir: Path = config["output_dir"]
    posts_dir = output_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    phash = _prompt_hash(_LIB_DIR / "persona.txt", PROMPTS_DIR / "system.txt", PROMPTS_DIR / "user.txt")

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

    total             = len(topics)
    success_count     = 0
    failed_count      = 0
    skipped_count     = 0
    consecutive_failures = 0

    for i, topic in enumerate(topics):
        slug    = topic["slug"]
        keyword = topic["keyword"]

        if state.is_done(slug):
            log(f"[{i+1}/{total}] SKIP {slug} (already completed)")
            skipped_count += 1
            continue

        log(f"[{i+1}/{total}] Generating: {keyword} ({topic['target_word_count']} words)...")

        try:
            content = with_retry(
                lambda t=topic: generate_ai(t, config),
                max_retries=config["max_retries"],
                label=slug,
            )
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                log(f"  ERROR: HTTP {e.code} — API key rejected.")
                log("  Get or rotate your key at: https://platform.openai.com/api-keys")
                log("  Then update API_KEY in blogs.env or your environment.")
                sys.exit(1)
            code = error_code_for(e)
            log(f"  FAILED [{code}]: {slug}")
            state.record_failure(slug, e, config["max_retries"], code,
                                 id=topic.get("id"), keyword=keyword, title=topic["title"])
            failed_count += 1
            consecutive_failures += 1
        except Exception as e:
            code = error_code_for(e)
            log(f"  FAILED [{code}]: {slug}")
            state.record_failure(slug, e, config["max_retries"], code,
                                 id=topic.get("id"), keyword=keyword, title=topic["title"])
            failed_count += 1
            consecutive_failures += 1
        else:
            out_path = posts_dir / f"{slug}.md"
            try:
                atomic_write(out_path, content)
            except Exception as e:
                log(f"  ERROR [WRITE_ERROR]: Could not write {out_path} — {e}")
                state.record_failure(slug, e, 0, "WRITE_ERROR",
                                     id=topic.get("id"), keyword=keyword, title=topic["title"])
                failed_count += 1
                consecutive_failures += 1
                if not config["continue_on_error"]:
                    log("  Stopping (continue_on_error=false).")
                    break
                continue

            state.record_success(slug, out_path, phash,
                                 id=topic.get("id"), keyword=keyword, title=topic["title"], mode="ai")
            success_count += 1
            consecutive_failures = 0
            log(f"  OK -> {out_path}")

            delay_s  = config["delay_ms"] / 1000.0
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
    state.write_summary(total=total, success=success_count, failed=failed_count,
                        skipped=skipped_count, mode="ai")
    log(f"Done. total={total} success={success_count} "
        f"failed={failed_count} skipped={skipped_count}")


if __name__ == "__main__":
    run()
