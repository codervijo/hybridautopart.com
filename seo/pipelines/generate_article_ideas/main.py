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
        "use_ai":         os.environ.get("USE_AI", "false").lower() == "true",
        "api_key":        os.environ.get("API_KEY", ""),
        "model":          os.environ.get("MODEL", "gpt-4.1-mini"),
        "api_url":        os.environ.get("API_URL", "https://api.openai.com/v1/chat/completions"),
        "max_tokens":     int(os.environ.get("MAX_TOKENS", "4096")),
        "ideas_per_seed": int(os.environ.get("IDEAS_PER_SEED", "8")),
        "batch_size":     int(os.environ.get("BATCH_SIZE", "10")),
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
        "title":                    keyword_to_title(kw),
        "primary_keyword":          kw,
        "search_intent":            classify_intent(kw),
        "slug":                     slugify(kw),
        "target_word_count":        target_word_count(kw, default_wc),
        "cluster":                  "",
        "priority":                 "Medium",
        "suggested_internal_links": [],
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
# AI idea generation
# ---------------------------------------------------------------------------

def _extract_json_array(text: str) -> list:
    """Parse a JSON array from LLM output, tolerating markdown code fences."""
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def _normalize_ai_idea(raw: dict, idx: int, default_wc: int) -> dict | None:
    """Coerce an LLM-generated idea dict into the standard schema."""
    keyword = (
        raw.get("primary_keyword") or raw.get("keyword") or raw.get("title", "")
    ).strip().lower()
    if not keyword:
        return None

    title = (raw.get("title") or keyword_to_title(keyword)).strip()
    slug  = slugify(raw.get("slug") or keyword) or f"idea-{idx}"

    intent = raw.get("search_intent", "").strip()
    if intent not in {"Informational", "Commercial", "Comparison", "Transactional"}:
        intent = classify_intent(keyword)

    try:
        wc = int(raw["target_word_count"])
    except (KeyError, ValueError, TypeError):
        wc = target_word_count(keyword, default_wc)

    priority = raw.get("priority", "Medium").strip()
    if priority not in {"High", "Medium", "Low"}:
        priority = "Medium"

    links = raw.get("suggested_internal_links") or []
    if not isinstance(links, list):
        links = []

    return {
        "title":                    title,
        "primary_keyword":          normalize(keyword),
        "search_intent":            intent,
        "slug":                     slug,
        "target_word_count":        wc,
        "cluster":                  raw.get("cluster", "").strip(),
        "priority":                 priority,
        "suggested_internal_links": [str(l).strip() for l in links if l],
    }


def _call_api_with_retry(fn, max_retries: int, label: str):
    """Call fn() with exponential backoff; raises on final failure."""
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
            log(f"  RETRY [{attempt + 1}/{max_retries}] {label} — HTTP {e.code}, waiting {wait:.1f}s")
        except Exception as e:
            last_error = e
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"  RETRY [{attempt + 1}/{max_retries}] {label} — {type(e).__name__}: {e}, waiting {wait:.1f}s")
        attempt += 1
        if attempt <= max_retries:
            time.sleep(wait)
    raise last_error


def generate_ai_ideas(seeds: list[str], config: dict) -> list[dict]:
    """Call the LLM in batches to generate enriched article ideas for all seeds."""
    batch_size    = config["batch_size"]
    ideas_per_seed = config["ideas_per_seed"]
    default_wc    = config["default_word_count"]
    batches       = [seeds[i:i + batch_size] for i in range(0, len(seeds), batch_size)]
    all_ideas: list[dict] = []

    log(f"AI mode: {len(seeds)} seed(s) across {len(batches)} batch(es), "
        f"{ideas_per_seed} ideas/seed")

    for b_idx, batch in enumerate(batches):
        seeds_text  = "\n".join(f"- {s}" for s in batch)
        user_prompt = Template(load_prompt("user")).substitute(
            ideas_per_seed=ideas_per_seed,
            seeds=seeds_text,
        )

        payload = json.dumps({
            "model":    config["model"],
            "messages": [
                {"role": "system", "content": load_prompt("system")},
                {"role": "user",   "content": user_prompt},
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

        log(f"[{b_idx + 1}/{len(batches)}] Calling API for {len(batch)} seed(s)…")

        try:
            raw_text = _call_api_with_retry(
                lambda r=req: _chat_response(r, config["timeout"]),
                max_retries=config["max_retries"],
                label=f"batch-{b_idx + 1}",
            )
        except Exception as e:
            log(f"  ERROR: batch {b_idx + 1} failed — {e}")
            continue

        try:
            raw_ideas = _extract_json_array(raw_text)
        except (json.JSONDecodeError, ValueError) as e:
            log(f"  ERROR: could not parse JSON from batch {b_idx + 1} — {e}")
            log(f"  Response (first 300 chars): {raw_text[:300]}")
            continue

        count = 0
        for idx, raw in enumerate(raw_ideas):
            if not isinstance(raw, dict):
                continue
            idea = _normalize_ai_idea(raw, len(all_ideas) + idx, default_wc)
            if idea:
                all_ideas.append(idea)
                count += 1
        log(f"  Parsed {count} idea(s)")

        if b_idx < len(batches) - 1:
            _sleep(config)

    return all_ideas


def _chat_response(req: urllib.request.Request, timeout: int) -> str:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read().decode())
    return result["choices"][0]["message"]["content"]


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

    if config["use_ai"]:
        if not config["api_key"] or config["api_key"] == "your_key_here":
            log("ERROR: API_KEY is not set in ideas.env")
            sys.exit(1)
        ideas = generate_ai_ideas(seeds, config)
    else:
        all_keywords: list[str] = []

        for i, seed in enumerate(seeds):
            log(f"[{i + 1}/{len(seeds)}] Expanding: {seed}")

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
