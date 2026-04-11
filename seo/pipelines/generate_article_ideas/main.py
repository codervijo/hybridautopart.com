#!/usr/bin/env python3
"""
SEO Article Idea Generator
Generates content ideas from seed keywords via autocomplete expansion and
pattern-based expansion. Writes structured JSON to output/ideas.json.
"""

import json
import os
import re
import sys
import time
import random
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_env_file(path="ideas.env"):
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
        "input_dir": Path(os.environ.get("INPUT_DIR", "input")),
        "output_dir": Path(os.environ.get("OUTPUT_DIR", "output")),
        "use_autocomplete": os.environ.get("USE_AUTOCOMPLETE", "true").lower() == "true",
        "autocomplete_az": os.environ.get("AUTOCOMPLETE_AZ", "true").lower() == "true",
        "autocomplete_modifiers": os.environ.get("AUTOCOMPLETE_MODIFIERS", "true").lower() == "true",
        "use_patterns": os.environ.get("USE_PATTERNS", "true").lower() == "true",
        "delay_ms": int(os.environ.get("DELAY_MS", "500")),
        "jitter_ms": int(os.environ.get("JITTER_MS", "300")),
        "max_retries": int(os.environ.get("MAX_RETRIES", "3")),
        "timeout": int(os.environ.get("TIMEOUT", "10")),
        "default_word_count": int(os.environ.get("DEFAULT_WORD_COUNT", "1200")),
    }


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------

def load_seeds_from_txt(path: Path) -> list[str]:
    seeds = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                seeds.append(line)
    return seeds


def load_seeds_from_json(path: Path) -> list[str]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    def extract(item) -> str:
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return (
                item.get("keyword")
                or item.get("seed")
                or item.get("primary_keyword")
                or ""
            ).strip()
        return ""

    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        raw = data.get("seeds") or data.get("keywords") or []
    else:
        raw = []

    return [s for s in (extract(item) for item in raw) if s]


def load_all_seeds(input_dir: Path) -> list[str]:
    if not input_dir.exists():
        log(f"WARN: input dir {input_dir} does not exist — no seeds loaded")
        return []

    seeds: list[str] = []

    for path in sorted(input_dir.glob("*.txt")):
        try:
            batch = load_seeds_from_txt(path)
            log(f"Loaded {len(batch)} seed(s) from {path.name}")
            seeds.extend(batch)
        except Exception as e:
            log(f"WARN: could not read {path.name}: {e}")

    for path in sorted(input_dir.glob("*.json")):
        try:
            batch = load_seeds_from_json(path)
            log(f"Loaded {len(batch)} seed(s) from {path.name}")
            seeds.extend(batch)
        except Exception as e:
            log(f"WARN: could not read {path.name}: {e}")

    # Normalize + deduplicate seeds
    seen: set[str] = set()
    unique: list[str] = []
    for s in seeds:
        n = normalize(s)
        if n and n not in seen:
            seen.add(n)
            unique.append(n)

    return unique


# ---------------------------------------------------------------------------
# Normalization & slug
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def keyword_to_title(keyword: str) -> str:
    stop_words = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at",
        "to", "for", "of", "with", "by", "from", "is", "are",
    }
    words = keyword.strip().split()
    return " ".join(
        w.capitalize() if i == 0 or w.lower() not in stop_words else w.lower()
        for i, w in enumerate(words)
    )


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

_INTENT_RULES: list[tuple[list[str], str]] = [
    (["vs", "versus", "compare", "difference between", " or "], "Comparison"),
    (["buy", "price", "cost", "cheap", "affordable", "deal", "discount", "near me", "for sale", "shop"], "Transactional"),
    (["best", "top", "review", "reviews", "rated", "recommend", "worth it"], "Commercial"),
    (["how", "why", "what", "when", "where", "which", "does", "do", "can", "will", "should"], "Informational"),
]


def classify_intent(keyword: str) -> str:
    kw = keyword.lower()
    for triggers, intent in _INTENT_RULES:
        for trigger in triggers:
            if re.search(r"\b" + re.escape(trigger.strip()) + r"\b", kw):
                return intent
    return "Informational"


def target_word_count(keyword: str, default: int) -> int:
    intent = classify_intent(keyword)
    return {
        "Informational": 1500,
        "Commercial":    1800,
        "Comparison":    2000,
        "Transactional":  800,
    }.get(intent, default)


# ---------------------------------------------------------------------------
# Autocomplete expansion
# ---------------------------------------------------------------------------

_AUTOCOMPLETE_URL = (
    "https://suggestqueries.google.com/complete/search?client=firefox&q={query}"
)

_AZ = list("abcdefghijklmnopqrstuvwxyz")
_MODIFIERS = ["how", "why", "best", "cost", "vs", "problems", "is", "what", "when"]


def fetch_autocomplete(query: str, timeout: int) -> list[str]:
    url = _AUTOCOMPLETE_URL.format(query=urllib.parse.quote(query))
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; SEO-idea-generator/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
        return [s.strip() for s in data[1] if isinstance(s, str) and s.strip()]
    return []


def with_retry(fn, max_retries: int, label: str) -> list[str]:
    attempt = 0
    last_error: Exception | None = None
    while attempt <= max_retries:
        try:
            return fn()
        except Exception as e:
            last_error = e
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"  RETRY [{attempt + 1}/{max_retries}] {label} — {type(e).__name__}: {e}, waiting {wait:.1f}s")
            attempt += 1
            if attempt <= max_retries:
                time.sleep(wait)
    log(f"  WARN: gave up on {label}: {last_error}")
    return []


def _sleep(config: dict):
    d = config["delay_ms"] / 1000.0 + random.uniform(0, config["jitter_ms"] / 1000.0)
    if d > 0:
        time.sleep(d)


def expand_autocomplete(seed: str, config: dict) -> list[str]:
    results: list[str] = []
    timeout = config["timeout"]
    max_retries = config["max_retries"]

    # A–Z: "{seed} a", "{seed} b", ...
    if config["autocomplete_az"]:
        for ch in _AZ:
            query = f"{seed} {ch}"
            results.extend(with_retry(
                lambda q=query: fetch_autocomplete(q, timeout),
                max_retries=max_retries,
                label=query,
            ))
            _sleep(config)

    # Modifier prefixes: "how {seed}", "why {seed}", ...
    if config["autocomplete_modifiers"]:
        for mod in _MODIFIERS:
            query = f"{mod} {seed}"
            results.extend(with_retry(
                lambda q=query: fetch_autocomplete(q, timeout),
                max_retries=max_retries,
                label=query,
            ))
            _sleep(config)

    return results


# ---------------------------------------------------------------------------
# Pattern-based expansion
# ---------------------------------------------------------------------------

_PATTERNS = [
    "how to {seed}",
    "why does {seed}",
    "why is {seed} important",
    "what is {seed}",
    "what causes {seed}",
    "best {seed}",
    "top {seed}",
    "{seed} problems",
    "problems with {seed}",
    "is {seed} worth it",
    "cost of {seed}",
    "{seed} cost",
    "how much does {seed} cost",
    "{seed} repair",
    "{seed} replacement",
    "{seed} symptoms",
    "{seed} diagnosis",
    "{seed} diy",
    "{seed} near me",
    "how long does {seed} last",
    "when to replace {seed}",
    "{seed} warning signs",
    "{seed} vs oem",
    "{seed} for hybrid vehicles",
    "signs of bad {seed}",
]


def expand_patterns(seed: str) -> list[str]:
    return [p.replace("{seed}", seed) for p in _PATTERNS]


# ---------------------------------------------------------------------------
# Idea construction & deduplication
# ---------------------------------------------------------------------------

def build_idea(keyword: str, default_wc: int) -> dict:
    kw = normalize(keyword)
    return {
        "title": keyword_to_title(kw),
        "primary_keyword": kw,
        "search_intent": classify_intent(kw),
        "slug": slugify(kw),
        "target_word_count": target_word_count(kw, default_wc),
    }


def deduplicate(ideas: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for idea in ideas:
        key = idea["slug"]
        if key not in seen:
            seen.add(key)
            unique.append(idea)
    return unique


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_output(output_dir: Path, ideas: list[dict]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "ideas.json"
    out_path.write_text(json.dumps(ideas, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(out_path, 0o666)
    return out_path


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    config = get_config()

    seeds = load_all_seeds(config["input_dir"])
    if not seeds:
        log("ERROR: No seeds found. Add .txt or .json files to input/")
        sys.exit(1)

    log(f"Loaded {len(seeds)} unique seed(s)")

    all_keywords: list[str] = []

    for i, seed in enumerate(seeds):
        log(f"[{i + 1}/{len(seeds)}] Expanding: {seed}")

        # Always include the seed itself
        all_keywords.append(seed)

        if config["use_patterns"]:
            patterns = expand_patterns(seed)
            log(f"  patterns: {len(patterns)}")
            all_keywords.extend(patterns)

        if config["use_autocomplete"]:
            ac = expand_autocomplete(seed, config)
            log(f"  autocomplete: {len(ac)}")
            all_keywords.extend(ac)

    log(f"Total raw keywords: {len(all_keywords)}")

    ideas = [build_idea(kw, config["default_word_count"]) for kw in all_keywords if kw.strip()]
    ideas = deduplicate(ideas)

    log(f"Unique ideas after dedup: {len(ideas)}")

    out_path = write_output(config["output_dir"], ideas)
    log(f"Written → {out_path}")


if __name__ == "__main__":
    run()
