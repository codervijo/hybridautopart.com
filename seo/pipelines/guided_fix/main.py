#!/usr/bin/env python3
"""guided_fix — interactive AI-driven walkthrough of audit todo items.

Loads audit data, picks one item at a time (priority order), walks the user
through the fix conversationally via Claude. Captures successful fix paths
as playbooks for future sessions.

Resumable: completed items are tracked in data/reports/{today}/work-log.md.
On startup, items already marked done in that file are skipped.

Cost-controlled: tracked per call; soft cap per item, hard cap per session.
"""

import json
import os
import re
import string
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.audit_state import read_latest, today_str
from lib.env import load_env_file
from lib.io import atomic_write, log, utc_now

PROMPTS_DIR = Path(__file__).parent / "prompts"
PLAYBOOKS_DIR = Path(__file__).parent / "playbooks"
ITEM_DONE_TOKEN = "[ITEM_DONE]"

# Claude Sonnet 4.6 pricing as of Apr 2026. Override via env if model changes.
INPUT_PRICE_PER_MTOK = 3.00
OUTPUT_PRICE_PER_MTOK = 15.00

# Impact ranking — mirrors analyze_audit_results.CHECK_META, kept inline to
# avoid coupling. When this needs a third user, move to lib/audit_priorities.
_IMPACT = {
    "network_error": 5,
    "canonical_cross_language": 4, "thin_page": 4, "duplicate_cluster": 4,
    "orphan_page": 4, "title_h1_mismatch": 4, "missing_title": 4,
    "images_missing_alt": 1,
}


def _impact_for(issue_type: str) -> int:
    if issue_type in _IMPACT:
        return _IMPACT[issue_type]
    if issue_type.startswith("http_5"):
        return 5
    if issue_type.startswith("http_4"):
        return 4
    return 3  # default Medium


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def get_config() -> dict:
    load_env_file("../../seo.env", "guided.env")
    return {
        "data_root":           Path(os.environ.get("DATA_ROOT", "../../data")),
        "anthropic_api_key":   os.environ.get("ANTHROPIC_API_KEY", ""),
        "model":               os.environ.get("GUIDED_MODEL", "claude-sonnet-4-6"),
        "max_cost_session":    float(os.environ.get("MAX_COST_USD_PER_SESSION", "5.00")),
        "max_cost_item":       float(os.environ.get("MAX_COST_USD_PER_ITEM", "1.00")),
        "max_turns_per_item":  int(os.environ.get("MAX_TURNS_PER_ITEM", "30")),
        "item_filter":         os.environ.get("ITEM", "").strip(),
        "site":                os.environ.get("SITE_URL", "https://hybridautopart.com"),
    }


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

class CostTracker:
    def __init__(self, max_session: float, input_price: float, output_price: float) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0
        self.max_session = max_session
        self.input_price = input_price
        self.output_price = output_price

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.calls += 1

    @property
    def total(self) -> float:
        return ((self.input_tokens / 1_000_000) * self.input_price
                + (self.output_tokens / 1_000_000) * self.output_price)

    def session_exceeded(self) -> bool:
        return self.total >= self.max_session


# ---------------------------------------------------------------------------
# Anthropic API (stdlib urllib)
# ---------------------------------------------------------------------------

def call_claude(model: str, api_key: str, system: str, messages: list[dict],
                max_tokens: int = 1024, timeout: int = 60) -> tuple[str, dict]:
    """Single-shot call. Returns (assistant_text, usage_dict)."""
    payload = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e

    text = "".join(b.get("text", "") for b in result.get("content", []) if b.get("type") == "text")
    usage = {
        "input_tokens":  result.get("usage", {}).get("input_tokens", 0),
        "output_tokens": result.get("usage", {}).get("output_tokens", 0),
    }
    return text, usage


# ---------------------------------------------------------------------------
# Inputs / item construction
# ---------------------------------------------------------------------------

def collect_inputs(data_root: Path) -> dict:
    return {
        "crawl":           read_latest(data_root, "crawls"),
        "audit_technical": read_latest(data_root, "audits/technical"),
        "audit_content":   read_latest(data_root, "audits/content"),
    }


def build_items(inputs: dict) -> list[dict]:
    """Flatten audit findings into todo items. Sorted by impact desc."""
    items: list[dict] = []

    at = inputs.get("audit_technical")
    if at:
        by_type: dict[str, list[str]] = defaultdict(list)
        for issue in at.get("issues", []):
            by_type[issue["type"]].append(issue["url"])
        for issue_type, urls in by_type.items():
            urls = sorted(set(urls))
            count_suffix = f" ({len(urls)} pages)" if len(urls) > 1 else ""
            items.append({
                "slug":   issue_type,
                "type":   issue_type,
                "title":  f"{issue_type}{count_suffix}",
                "urls":   urls,
                "source": "audit_technical",
                "impact": _impact_for(issue_type),
            })

    ac = inputs.get("audit_content")
    if ac:
        thin = ac.get("thin_pages", [])
        if thin:
            items.append({
                "slug":   "thin_page",
                "type":   "thin_page",
                "title":  f"Thin pages ({len(thin)})",
                "urls":   [t["url"] for t in thin],
                "source": "audit_content",
                "impact": _impact_for("thin_page"),
            })
        for i, c in enumerate(ac.get("duplicate_clusters", []), start=1):
            slug = f"duplicate_cluster_{i}"
            items.append({
                "slug":   slug,
                "type":   "duplicate_cluster",
                "title":  f"Duplicate cluster #{i} (sim={c['max_similarity']}, {len(c['members'])} pages)",
                "urls":   c["members"],
                "source": "audit_content",
                "impact": _impact_for("duplicate_cluster"),
            })

    items.sort(key=lambda x: (-x["impact"], x["slug"]))
    return items


# ---------------------------------------------------------------------------
# Work log
# ---------------------------------------------------------------------------

_WORK_LOG_HEADER = """# Work Log — {today}

_Auto-appended by `guided_fix`. Each line is one item handled this session.
On next run, items marked `done` here are skipped._

"""


def load_completed(work_log: Path) -> set[str]:
    if not work_log.exists():
        return set()
    done: set[str] = set()
    line_re = re.compile(r"^- \[(?P<status>done)\] (?P<slug>\S+)")
    for line in work_log.read_text(encoding="utf-8").splitlines():
        m = line_re.match(line)
        if m:
            done.add(m.group("slug"))
    return done


def append_work_log(work_log: Path, item: dict, status: str, cost_usd: float | None = None) -> None:
    work_log.parent.mkdir(parents=True, exist_ok=True)
    if not work_log.exists():
        atomic_write(work_log, _WORK_LOG_HEADER.format(today=today_str()))
    line = f"- [{status}] {item['slug']} — {item['title']}"
    if cost_usd is not None:
        line += f" — cost ${cost_usd:.3f}"
    line += f" — {utc_now()}\n"
    with open(work_log, "a", encoding="utf-8") as f:
        f.write(line)


# ---------------------------------------------------------------------------
# Playbooks
# ---------------------------------------------------------------------------

def load_playbook(slug: str) -> str | None:
    """Look up playbook by issue type slug. Try exact slug, then 'type' fallback."""
    p = PLAYBOOKS_DIR / f"{slug}.md"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


# ---------------------------------------------------------------------------
# Conversation loop
# ---------------------------------------------------------------------------

def _prompt(prompt_str: str) -> str:
    try:
        return input(prompt_str).strip()
    except (EOFError, KeyboardInterrupt):
        print()  # newline after ^C
        return "quit"


def _build_initial_user_message(item: dict, inputs: dict, playbook: str | None, site: str) -> str:
    lines: list[str] = [
        f"# Issue: `{item['type']}`",
        f"\n**Site**: {site}",
        f"**Slug**: `{item['slug']}`",
        f"**Title**: {item['title']}",
        f"**Source**: {item['source']}",
        f"**Affected URLs**: {len(item['urls'])}",
        "",
        "URLs (capped at 15):",
    ]
    for url in item["urls"][:15]:
        lines.append(f"- {url}")
    if len(item["urls"]) > 15:
        lines.append(f"- ...and {len(item['urls']) - 15} more")

    crawl = inputs.get("crawl")
    if crawl and item["urls"]:
        first = item["urls"][0]
        page = next((p for p in crawl.get("pages", []) if p["url"] == first), None)
        if page:
            lines += [
                "",
                f"## Current state of {first}",
                f"- HTTP: {page.get('status')}",
                f"- Title: `{page.get('title', '')}`",
                f"- Meta description: `{page.get('meta_description', '')}`",
                f"- Canonical: `{page.get('canonical', '')}`",
                f"- H1: {page.get('h1', [])}",
                f"- Word count: {page.get('word_count', 0)}",
            ]

    if playbook:
        lines += [
            "",
            "## PLAYBOOK (your primary guidance)",
            "",
            "```markdown",
            playbook.rstrip(),
            "```",
            "",
            "Walk the user through. Adapt if reality diverges from the playbook.",
        ]
    else:
        lines += [
            "",
            "No playbook exists for this issue type yet — improvise from your SEO knowledge",
            "and the audit data above. The conversation will be saved as a draft playbook at",
            "session end.",
        ]

    lines += [
        "",
        "Begin with the very first instruction. One step. Wait for the user's reply.",
    ]
    return "\n".join(lines)


def walk_item(item: dict, inputs: dict, config: dict, cost: CostTracker) -> tuple[str, list[dict], float]:
    """Run the conversation for one item. Returns (status, messages, item_cost_usd).

    status ∈ {'done', 'skipped', 'quit', 'aborted', 'max_turns', 'error'}
    """
    system = (PROMPTS_DIR / "system.txt").read_text(encoding="utf-8")
    playbook = load_playbook(item["slug"])

    initial = _build_initial_user_message(item, inputs, playbook, config["site"])
    messages: list[dict] = [{"role": "user", "content": initial}]

    cost_at_start = cost.total

    for _turn in range(config["max_turns_per_item"]):
        if cost.session_exceeded():
            log("\n!! Session cost cap reached. Aborting item. !!")
            return "aborted", messages, cost.total - cost_at_start

        item_spent = cost.total - cost_at_start
        if item_spent > config["max_cost_item"]:
            ans = _prompt(f"\nThis item has cost ${item_spent:.2f}. Continue? [y/n]: ")
            if not ans.lower().startswith("y"):
                return "aborted", messages, item_spent

        try:
            assistant_text, usage = call_claude(
                config["model"], config["anthropic_api_key"], system, messages,
            )
        except Exception as e:
            log(f"\n!! API error: {e} !!")
            return "error", messages, cost.total - cost_at_start
        cost.add(usage["input_tokens"], usage["output_tokens"])

        clean = assistant_text.replace(ITEM_DONE_TOKEN, "").rstrip()
        log(f"\nAI: {clean}\n")
        messages.append({"role": "assistant", "content": assistant_text})

        if ITEM_DONE_TOKEN in assistant_text:
            log("    [✓] AI signalled item complete.")
            return "done", messages, cost.total - cost_at_start

        user_text = _prompt("> ")
        if user_text.lower() in ("quit", "q", "exit"):
            return "quit", messages, cost.total - cost_at_start
        if user_text.lower() in ("skip", "k"):
            return "skipped", messages, cost.total - cost_at_start
        if not user_text:
            user_text = "(no response — continue)"
        messages.append({"role": "user", "content": user_text})

    log(f"\n!! Max turns ({config['max_turns_per_item']}) reached. Aborting item. !!")
    return "max_turns", messages, cost.total - cost_at_start


# ---------------------------------------------------------------------------
# Playbook distillation + merge
# ---------------------------------------------------------------------------

def _transcript_text(messages: list[dict]) -> str:
    parts = []
    for m in messages:
        parts.append(f"### {m['role']}\n\n{m['content']}\n")
    return "\n".join(parts)


def distill_playbook(item: dict, messages: list[dict], config: dict, cost: CostTracker) -> str | None:
    template = (PROMPTS_DIR / "distill.txt").read_text(encoding="utf-8")
    prompt = string.Template(template).safe_substitute(
        issue_type=item["type"],
        site=config["site"],
        today=today_str(),
        transcript=_transcript_text(messages),
    )
    try:
        text, usage = call_claude(
            config["model"], config["anthropic_api_key"],
            system="You distill conversation transcripts into SEO playbooks. Output markdown only.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        cost.add(usage["input_tokens"], usage["output_tokens"])
        return text.strip()
    except Exception as e:
        log(f"!! Distill failed: {e} !!")
        return None


def merge_playbooks(existing: str, new: str, config: dict, cost: CostTracker) -> str | None:
    template = (PROMPTS_DIR / "merge.txt").read_text(encoding="utf-8")
    prompt = string.Template(template).safe_substitute(
        existing=existing, new=new, today=today_str(),
    )
    try:
        text, usage = call_claude(
            config["model"], config["anthropic_api_key"],
            system="You merge SEO playbooks. Output markdown only.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        cost.add(usage["input_tokens"], usage["output_tokens"])
        return text.strip()
    except Exception as e:
        log(f"!! Merge failed: {e} !!")
        return None


def offer_playbook_save(item: dict, messages: list[dict], config: dict, cost: CostTracker) -> None:
    log("\n--- Distilling playbook from this session ---")
    new_pb = distill_playbook(item, messages, config, cost)
    if not new_pb:
        return

    existing_path = PLAYBOOKS_DIR / f"{item['type']}.md"
    if existing_path.exists():
        log("\nA playbook already exists. Merging...")
        existing = existing_path.read_text(encoding="utf-8")
        merged = merge_playbooks(existing, new_pb, config, cost)
        candidate = merged or new_pb
    else:
        candidate = new_pb

    log("\n" + "=" * 70)
    log(candidate)
    log("=" * 70)

    ans = _prompt("\nSave this playbook? [y/n]: ")
    if ans.lower().startswith("y"):
        atomic_write(existing_path, candidate + "\n")
        log(f"Saved → {existing_path}")
    else:
        log("Discarded.")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def print_summary(cost: CostTracker, completed: int, skipped: int) -> None:
    log("\n=== Session summary ===")
    log(f"  Items completed: {completed}")
    log(f"  Items skipped:   {skipped}")
    log(f"  API calls:       {cost.calls}")
    log(f"  Tokens in/out:   {cost.input_tokens:,} / {cost.output_tokens:,}")
    log(f"  Cost:            ${cost.total:.3f}")
    log("=======================")


def run() -> None:
    config = get_config()

    if not config["anthropic_api_key"]:
        log("ERROR [CONFIG]: ANTHROPIC_API_KEY is not set in seo.env or guided.env")
        sys.exit(1)

    inputs = collect_inputs(config["data_root"])
    if not inputs["audit_technical"] and not inputs["audit_content"]:
        log("ERROR [NO_DATA]: no audit data found. Run `make audit-all` first.")
        sys.exit(1)

    items = build_items(inputs)
    if config["item_filter"]:
        items = [i for i in items if i["slug"] == config["item_filter"]]
        if not items:
            log(f"ERROR [NO_MATCH]: no item with slug '{config['item_filter']}'")
            sys.exit(1)

    today = today_str()
    work_log = config["data_root"] / "reports" / today / "work-log.md"
    completed_already = load_completed(work_log)
    items = [i for i in items if i["slug"] not in completed_already]

    if not items:
        log(f"All items already completed for {today}. Nothing to do.")
        return

    log(f"=== {len(items)} item(s) to walk through ===")
    log(f"    Cost cap: ${config['max_cost_session']:.2f} session, ${config['max_cost_item']:.2f}/item")
    log(f"    Model: {config['model']}")
    log(f"    Work log: {work_log}\n")

    cost = CostTracker(
        max_session=config["max_cost_session"],
        input_price=INPUT_PRICE_PER_MTOK,
        output_price=OUTPUT_PRICE_PER_MTOK,
    )
    completed_now = 0
    skipped_now = 0

    try:
        for i, item in enumerate(items, 1):
            if cost.session_exceeded():
                log("\n!! Session cost cap reached. Stopping. !!")
                break

            log(f"\n--- Item {i}/{len(items)}: {item['title']} (impact {item['impact']}) ---")

            ans = _prompt("Start (s), skip (k), or quit (q)? [s]: ") or "s"
            if ans.lower().startswith("q"):
                break
            if ans.lower().startswith("k"):
                append_work_log(work_log, item, status="skipped")
                skipped_now += 1
                continue

            status, messages, item_cost = walk_item(item, inputs, config, cost)
            append_work_log(work_log, item, status=status, cost_usd=item_cost)

            if status == "done":
                completed_now += 1
                offer_playbook_save(item, messages, config, cost)
            elif status == "skipped":
                skipped_now += 1
            elif status == "quit":
                break
    finally:
        print_summary(cost, completed_now, skipped_now)


if __name__ == "__main__":
    run()
