#!/usr/bin/env python3
"""
SEO Blog Post Generator
Supports template mode and AI mode (OpenAI-compatible API).
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
_SEO_ROOT = Path(__file__).parent
if str(_SEO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_SEO_ROOT))
from lib.prompts import validate_template_vars

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()

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
        "input_json": os.environ.get("INPUT_JSON", "topics.json"),
        "output_dir": Path(os.environ.get("OUTPUT_DIR", "output")),
        "use_ai": os.environ.get("USE_AI", "false").lower() == "true",
        "api_key": os.environ.get("API_KEY", ""),
        "model": os.environ.get("MODEL", "gpt-4.1-mini"),
        "api_url": os.environ.get("API_URL", "https://api.openai.com/v1/chat/completions"),
        "delay_ms": int(os.environ.get("DELAY_MS", "2000")),
        "jitter_ms": int(os.environ.get("JITTER_MS", "1000")),
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
# Content generation — template mode
# ---------------------------------------------------------------------------

def _faq_questions(keyword: str, intent: str) -> list[tuple[str, str]]:
    """Generate 4 generic FAQ entries based on the keyword."""
    kw = keyword_to_title(keyword)
    return [
        (
            f"What is {kw}?",
            f"{kw} refers to the concept, system, or component described in this article. "
            f"Understanding it helps you make better decisions about your hybrid vehicle.",
        ),
        (
            f"How does {kw} work?",
            f"The mechanism behind {kw} involves several integrated components working together "
            f"to deliver performance, efficiency, or reliability depending on the context.",
        ),
        (
            f"Is {kw} important for my vehicle?",
            f"Yes — {kw} is relevant to many hybrid owners because it directly affects "
            f"fuel economy, maintenance costs, and driving experience.",
        ),
        (
            f"How can I maintain or improve {kw}?",
            f"Regular inspections, following manufacturer guidelines, and staying informed "
            f"about recalls or service bulletins are the best ways to address {kw}.",
        ),
    ]


def generate_template(topic: dict) -> str:
    """Build a structured markdown post without an AI API."""
    title = topic["title"]
    keyword = topic["keyword"]
    slug = topic["slug"]
    intent = topic["search_intent"]
    links = topic["suggested_internal_links"]
    aeo = topic["aeo_snippet_target"]
    target_wc = topic["target_word_count"]

    # Rough section count to approach target word count
    # Each section ≈ 150–200 words; intro+faq ≈ 300 words
    section_count = max(3, (target_wc - 300) // 175)

    lines: list[str] = []

    # Front-matter
    lines += [
        f"# {title}",
        "",
        f"**Primary keyword:** {keyword}  ",
        f"**Search intent:** {intent}  ",
        f"**Cluster:** {topic['cluster']}  " if topic["cluster"] else "",
        "",
    ]

    # Quick answer / AEO snippet
    if aeo:
        lines += [
            "## Quick Answer",
            "",
            f"{title} — in plain terms, this refers to the technology, component, or process "
            f"that hybrid vehicle owners and technicians encounter regularly. "
            f"Understanding {keyword} helps you maintain your vehicle, diagnose issues early, "
            f"and get more value from your hybrid investment.",
            "",
        ]
    else:
        lines += [
            f"If you've been searching for information about **{keyword}**, "
            f"this guide covers everything you need to know — from the basics to practical tips.",
            "",
        ]

    # Introduction
    lines += [
        "## Introduction",
        "",
        f"Hybrid vehicles have transformed the automotive industry, and **{keyword}** is one of "
        f"the key topics that owners, mechanics, and enthusiasts frequently research. "
        f"Whether you're a first-time hybrid owner or a seasoned technician, "
        f"understanding this topic will help you make smarter decisions.",
        "",
        f"In this article, we'll walk through everything you need to know about {keyword}, "
        f"including how it works, why it matters, common issues to watch for, "
        f"and actionable steps you can take today.",
        "",
    ]

    # Dynamic H2 sections
    section_templates = [
        (
            f"How {title} Works",
            f"At its core, {keyword} operates through a combination of mechanical and electronic "
            f"systems designed to maximize efficiency. The main components interact in real time, "
            f"adjusting output based on driving conditions, battery state, and driver input. "
            f"Modern hybrid systems are engineered with redundancy so that a failure in one area "
            f"doesn't immediately disable the entire vehicle. "
            f"Knowing how these systems interact makes it much easier to identify problems early "
            f"and communicate clearly with a technician.",
        ),
        (
            f"Why {title} Matters for Hybrid Owners",
            f"For hybrid vehicle owners, {keyword} is directly tied to fuel efficiency, "
            f"long-term reliability, and resale value. Neglecting this area can lead to "
            f"reduced performance, unexpected repair bills, and in some cases, safety concerns. "
            f"On the other hand, staying informed and proactive about {keyword} typically "
            f"extends the lifespan of your vehicle and lowers your total cost of ownership.",
        ),
        (
            f"Common Issues Related to {title}",
            f"There are several issues that hybrid owners commonly encounter with {keyword}. "
            f"These range from minor warning lights and sensor errors to more significant "
            f"mechanical or electrical faults. Early detection is key — most problems related "
            f"to {keyword} are much less expensive to fix when caught before they escalate. "
            f"If you notice unusual behavior, unusual sounds, or dashboard warnings, "
            f"consult a certified hybrid technician promptly.",
        ),
        (
            f"Diagnosing Problems with {title}",
            f"Proper diagnosis of {keyword} issues requires a combination of OBD-II scanning, "
            f"visual inspection, and knowledge of your specific vehicle model. "
            f"Many issues are model-specific, so consulting your vehicle's service manual or "
            f"a factory-trained technician is recommended. Generic code readers can provide "
            f"a starting point, but they may miss hybrid-specific fault codes that require "
            f"dedicated scan tools.",
        ),
        (
            f"Repair and Replacement Options for {title}",
            f"Repair options for {keyword} vary widely in cost and complexity. "
            f"Some tasks — like cleaning sensors or replacing minor components — can be handled "
            f"by experienced DIYers. Others require specialist equipment and should only be "
            f"performed by certified technicians. When sourcing replacement parts, "
            f"OEM parts are generally preferred for hybrid systems due to the tight tolerances "
            f"and software integration required. Aftermarket options exist but vary in quality.",
        ),
        (
            f"Cost of {title}: What to Expect",
            f"The cost associated with {keyword} depends heavily on the make, model, year, "
            f"and severity of the issue. Minor repairs may cost less than $200, "
            f"while major component replacements can run into the thousands. "
            f"Always get at least two quotes from reputable shops, and ask whether the repair "
            f"comes with a warranty. For older vehicles, weigh the repair cost against the "
            f"vehicle's current market value before proceeding.",
        ),
        (
            f"Maintenance Tips to Prevent {title} Problems",
            f"Preventive maintenance is the most cost-effective strategy for managing {keyword}. "
            f"Follow the manufacturer's recommended service intervals, keep your battery "
            f"management system healthy, and address warning lights immediately rather than "
            f"deferring them. Annual inspections by a hybrid specialist — even when no warning "
            f"lights are present — can catch developing issues before they become expensive.",
        ),
        (
            f"When to Seek Professional Help with {title}",
            f"While general maintenance can often be handled at home, {keyword} issues that "
            f"involve high-voltage systems, complex software recalibration, or safety-critical "
            f"components should always be handled by a certified professional. "
            f"Working on hybrid high-voltage systems without proper training and equipment "
            f"is dangerous. When in doubt, consult a Toyota-certified or hybrid-specialist shop.",
        ),
    ]

    for i in range(min(section_count, len(section_templates))):
        heading, body = section_templates[i]
        lines += [f"## {heading}", "", body, ""]

    # Internal links section
    if links:
        lines += ["## Related Resources", ""]
        for link in links:
            link_title = keyword_to_title(link.replace("-", " "))
            lines.append(f"- [{link_title}](/{link}/)")
        lines.append("")

    # FAQ
    lines += ["## Frequently Asked Questions", ""]
    for question, answer in _faq_questions(keyword, intent):
        lines += [f"### {question}", "", answer, ""]

    # Conclusion
    lines += [
        "## Conclusion",
        "",
        f"Understanding **{keyword}** is an important part of owning and maintaining a hybrid "
        f"vehicle. Whether you're troubleshooting an issue, planning preventive maintenance, "
        f"or simply trying to learn more about how your car works, the information in this "
        f"guide gives you a solid foundation.",
        "",
        f"If you found this article helpful, explore our other guides on hybrid vehicle "
        f"maintenance, repair, and ownership to get the most out of your investment.",
        "",
    ]

    return "\n".join(line for line in lines)


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
    validate_template_vars(tmpl, vars_, label="prompts/user.txt")
    return Template(tmpl).substitute(vars_)


def generate_ai(topic: dict, config: dict) -> str:
    """Call an OpenAI-compatible chat completions endpoint."""
    import json as _json

    payload = _json.dumps({
        "model": config["model"],
        "messages": [
            {"role": "system", "content": load_prompt("system")},
            {"role": "user", "content": _build_prompt(topic)},
        ],
        "temperature": 0.7,
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
        try:
            return fn()
        except urllib.error.HTTPError as e:
            last_error = e
            code = e.code
            # Don't retry auth errors
            if code in (401, 403):
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"RETRY [{attempt + 1}/{max_retries}] {label} — HTTP {code}, waiting {wait:.1f}s")
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

    def record_success(self, topic: dict, output_path: Path, mode: str):
        record = {
            "id": topic.get("id"),
            "keyword": topic["keyword"],
            "title": topic["title"],
            "slug": topic["slug"],
            "output_path": str(output_path),
            "mode": mode,
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
    output_dir: Path = config["output_dir"]
    posts_dir = output_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    mode = "ai" if config["use_ai"] else "template"

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

    log(f"Loaded {len(topics)} topic(s) from {input_path} — mode: {mode}")

    state = RunState(output_dir)

    total = len(topics)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    consecutive_failures = 0

    for i, topic in enumerate(topics):
        slug = topic["slug"]
        title = topic["title"]
        keyword = topic["keyword"]

        # Resume: skip already completed
        if state.is_done(slug):
            log(f"SKIP: {slug} (already completed)")
            skipped_count += 1
            continue

        log(f"START: {keyword}")

        retry_count = 0

        def generate():
            if config["use_ai"]:
                return generate_ai(topic, config)
            return generate_template(topic)

        try:
            content = with_retry(
                generate,
                max_retries=config["max_retries"],
                label=slug,
            )
            retry_count = 0  # success
        except Exception as e:
            code = error_code_for(e)
            log(f"ERROR [{code}]: {slug} — {e}")
            state.record_failure(topic, e, config["max_retries"], code)
            failed_count += 1
            consecutive_failures += 1

            if consecutive_failures >= config["max_consecutive_failures"]:
                log(f"ERROR [MAX_FAILURES]: Reached {consecutive_failures} consecutive failures. Stopping.")
                break

            if not config["continue_on_error"]:
                log("ERROR [ABORT]: continue_on_error=false. Stopping.")
                break

            continue

        # Write post file atomically
        out_path = posts_dir / f"{slug}.md"
        try:
            atomic_write(out_path, content)
        except Exception as e:
            log(f"ERROR [WRITE_ERROR]: Could not write {out_path} — {e}")
            state.record_failure(topic, e, 0, "WRITE_ERROR")
            failed_count += 1
            consecutive_failures += 1
            if not config["continue_on_error"]:
                break
            continue

        state.record_success(topic, out_path, mode)
        success_count += 1
        consecutive_failures = 0
        log(f"SUCCESS: {slug}")

        # Delay after every post
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
        mode=mode,
    )

    log(
        f"\nDone. total={total} success={success_count} "
        f"failed={failed_count} skipped={skipped_count}"
    )


if __name__ == "__main__":
    run()
