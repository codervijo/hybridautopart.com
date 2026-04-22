#!/usr/bin/env python3
"""
SEO Image Generator
Processes Markdown blog posts, generates image prompts, optionally generates
images via an OpenAI-compatible API, and embeds them into the post.

Input:  input/posts/<slug>.md  OR  input/posts/<slug>/article.md
Output: output/posts/<slug>/article.md + images/ + prompts.json + manifest.json
"""

import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from string import Template

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.env import load_env_file
from lib.http import with_retry
from lib.io import atomic_write, atomic_write_bytes, log, utc_now
from lib.prompts import prompt_hash as _prompt_hash


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def get_config() -> dict:
    load_env_file("../../seo.env", "images.env")
    return {
        "input_dir":        Path(os.environ.get("INPUT_DIR", "input")),
        "output_dir":       Path(os.environ.get("OUTPUT_DIR", "output/posts")),
        "use_image_ai":     os.environ.get("USE_IMAGE_AI", "false").lower() == "true",
        "image_api_key":    os.environ.get("IMAGE_API_KEY", ""),
        "image_api_url":    os.environ.get("IMAGE_API_URL", "https://api.openai.com/v1/images/generations"),
        "image_model":      os.environ.get("IMAGE_MODEL", "dall-e-3"),
        "image_size":       os.environ.get("IMAGE_SIZE", "1792x1024"),
        "max_retries":      int(os.environ.get("MAX_RETRIES", "3")),
        "timeout":          int(os.environ.get("TIMEOUT", "60")),
        "continue_on_error": os.environ.get("CONTINUE_ON_ERROR", "true").lower() == "true",
        "delay_ms":         int(os.environ.get("DELAY_MS", "2000")),
        "jitter_ms":        int(os.environ.get("JITTER_MS", "500")),
    }


# ---------------------------------------------------------------------------
# Input discovery
# ---------------------------------------------------------------------------

def _scan_dir(directory: Path) -> list[tuple[str, Path]]:
    """
    Scan a single directory for posts. Supports:
      <slug>.md
      <slug>/article.md
    """
    posts: list[tuple[str, Path]] = []
    for item in sorted(directory.iterdir()):
        if item.is_file() and item.suffix == ".md":
            posts.append((item.stem, item))
        elif item.is_dir() and item.name != "posts":
            article = item / "article.md"
            if article.exists():
                posts.append((item.name, article))
    return posts


def discover_posts(input_dir: Path) -> list[tuple[str, Path]]:
    """
    Return [(slug, md_path), ...] discovered from input_dir.

    Auto-detects both layouts so either of these work without extra config:
      input/<slug>.md                   (INPUT_DIR=input)
      input/posts/<slug>.md             (INPUT_DIR=input  OR  INPUT_DIR=input/posts)
      input/<slug>/article.md
      input/posts/<slug>/article.md
    """
    if not input_dir.exists():
        return []

    posts: list[tuple[str, Path]] = []
    seen_slugs: set[str] = set()

    # Scan input_dir itself
    for slug, path in _scan_dir(input_dir):
        if slug not in seen_slugs:
            posts.append((slug, path))
            seen_slugs.add(slug)

    # Also scan input_dir/posts/ if it exists (avoids needing to change INPUT_DIR)
    posts_subdir = input_dir / "posts"
    if posts_subdir.is_dir():
        for slug, path in _scan_dir(posts_subdir):
            if slug not in seen_slugs:
                posts.append((slug, path))
                seen_slugs.add(slug)

    return sorted(posts, key=lambda t: t[0])


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------

def parse_markdown(content: str) -> dict:
    """
    Extract:
      title     — first H1 (# …)
      keyword   — value of **Primary keyword:** front-matter line
      h2_sections — all ## headings in order
      topic     — keyword if present, else title
    """
    title = ""
    keyword = ""
    h2_sections: list[str] = []

    for line in content.splitlines():
        if not title and re.match(r"^# (?!#)", line):
            title = line[2:].strip()
        if not keyword and line.startswith("**Primary keyword:**"):
            keyword = line.replace("**Primary keyword:**", "").strip()
        if re.match(r"^## (?!#)", line):
            h2_sections.append(line[3:].strip())

    return {
        "title": title,
        "keyword": keyword,
        "topic": keyword or title,
        "h2_sections": h2_sections,
    }


# ---------------------------------------------------------------------------
# Prompt generation
# ---------------------------------------------------------------------------

def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()


def _load_prompt_list(name: str) -> list[str]:
    """Load a multi-template .txt file split by '---' separators."""
    raw = (_PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")
    return [t.strip() for t in raw.split("---") if t.strip()]


# Skip generic sections that don't map to useful diagrams
_SKIP_SECTIONS = frozenset({
    "introduction", "conclusion", "quick answer",
    "frequently asked questions", "related resources",
})


def _pick_supporting_h2s(h2_sections: list[str], min_count: int = 2, max_count: int = 4) -> list[str]:
    """Select content-rich H2s to illustrate."""
    filtered = [h for h in h2_sections if h.lower() not in _SKIP_SECTIONS]
    # Fall back to all sections if filtering leaves fewer than min_count
    pool = filtered if len(filtered) >= min_count else h2_sections
    return pool[:max_count]


def generate_prompts(parsed: dict) -> dict:
    topic = parsed["topic"]
    style = _load_prompt("style")
    templates = _load_prompt_list("supporting")

    featured = Template(_load_prompt("featured")).substitute(topic=topic, style=style)

    selected_h2s = _pick_supporting_h2s(parsed["h2_sections"])
    images = []
    for i, section in enumerate(selected_h2s):
        tmpl = templates[i % len(templates)]
        images.append({
            "name": f"diagram-{i + 1}",
            "section": section,
            "prompt": Template(tmpl).substitute(section=section, style=style),
        })

    return {"featured": featured, "images": images}


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

def _placeholder_svg(label: str, width: int = 1200, height: int = 630) -> bytes:
    safe = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f'  <rect width="{width}" height="{height}" fill="#f8f9fa"/>\n'
        f'  <rect x="2" y="2" width="{width-4}" height="{height-4}" '
        f'fill="none" stroke="#dee2e6" stroke-width="2" stroke-dasharray="8,4"/>\n'
        f'  <text x="{width//2}" y="{height//2 - 12}" font-family="system-ui,sans-serif" '
        f'font-size="20" fill="#6c757d" text-anchor="middle">{safe}</text>\n'
        f'  <text x="{width//2}" y="{height//2 + 18}" font-family="system-ui,sans-serif" '
        f'font-size="14" fill="#adb5bd" text-anchor="middle">Placeholder — image not generated</text>\n'
        f'</svg>'
    )
    return svg.encode("utf-8")


def _call_image_api(prompt: str, config: dict) -> bytes:
    payload = json.dumps({
        "model":           config["image_model"],
        "prompt":          prompt,
        "n":               1,
        "size":            config["image_size"],
        "response_format": "url",
    }).encode()

    req = urllib.request.Request(
        config["image_api_url"],
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {config['image_api_key']}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=config["timeout"]) as resp:
        result = json.loads(resp.read().decode())

    image_url = result["data"][0]["url"]

    with urllib.request.urlopen(image_url, timeout=config["timeout"]) as img_resp:
        return img_resp.read()


def generate_image(name: str, prompt: str, images_dir: Path, config: dict) -> str:
    """
    Generate one image. Returns 'ai' or 'placeholder'.
    Writes result to images_dir/<name>.webp atomically.
    """
    out_path = images_dir / f"{name}.webp"

    if config["use_image_ai"]:
        data = with_retry(
            lambda: _call_image_api(prompt, config),
            max_retries=config["max_retries"],
            label=name,
        )
        mode = "ai"
    else:
        data = _placeholder_svg(name)
        mode = "placeholder"

    atomic_write_bytes(out_path, data)
    return mode


# ---------------------------------------------------------------------------
# Markdown embedding
# ---------------------------------------------------------------------------

def _img_tag(name: str, alt: str) -> str:
    return f"![{alt}](images/{name}.webp)"


def embed_images(content: str, parsed: dict, prompts: dict) -> str:
    """
    - Insert featured image block immediately after the H1 line.
    - Insert each supporting image after its matching H2 section heading.
    - Any unmatched supporting images are placed after evenly-spaced H2s.
    """
    lines = content.splitlines()
    result: list[str] = []
    keyword = parsed["keyword"] or parsed["topic"]

    featured_done = False
    supporting = list(prompts["images"])   # [{name, section, prompt}]
    placed: set[str] = set()

    def insert_image(name: str, alt: str) -> None:
        result.append("")
        result.append(_img_tag(name, alt))
        result.append("")

    for line in lines:
        result.append(line)

        # Featured: after H1
        if not featured_done and re.match(r"^# (?!#)", line):
            alt = f"{parsed['title']} — hybrid vehicle technical overview diagram"
            insert_image("featured", alt)
            log(f"  EMBEDDED: featured after H1")
            featured_done = True
            continue

        # Supporting: after matching H2
        if re.match(r"^## (?!#)", line):
            section_name = line[3:].strip().lower()
            for img in supporting:
                if img["name"] in placed:
                    continue
                img_section = img["section"].lower()
                # Match if either string contains the other (handles prefix/suffix cases)
                if img_section in section_name or section_name in img_section:
                    alt = f"{img['section']} diagram — {keyword}"
                    insert_image(img["name"], alt)
                    log(f"  EMBEDDED: {img['name']} after H2 \"{img['section']}\"")
                    placed.add(img["name"])
                    break

    # Evenly place any remaining unmatched supporting images
    remaining = [img for img in supporting if img["name"] not in placed]
    if remaining:
        h2_positions = [i for i, ln in enumerate(result) if re.match(r"^## (?!#)", ln)]
        step = max(1, len(h2_positions) // (len(remaining) + 1))
        targets = [h2_positions[min(i * step, len(h2_positions) - 1)] for i in range(1, len(remaining) + 1)]

        # Insert in reverse to preserve indices
        for img, idx in zip(remaining, sorted(targets, reverse=True)):
            alt = f"{img['section']} diagram — {keyword}"
            result.insert(idx + 1, "")
            result.insert(idx + 2, _img_tag(img["name"], alt))
            result.insert(idx + 3, "")
            log(f"  EMBEDDED: {img['name']} (evenly spaced, near H2 index {idx})")

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def write_manifest(post_dir: Path, slug: str, parsed: dict, image_records: list[dict], mode: str) -> None:
    manifest = {
        "slug":         slug,
        "title":        parsed["title"],
        "keyword":      parsed["keyword"],
        "mode":         mode,
        "prompt_hash":  _prompt_hash(
            _PROMPTS_DIR / "style.txt",
            _PROMPTS_DIR / "featured.txt",
            _PROMPTS_DIR / "supporting.txt",
        ),
        "images":       image_records,
        "generated_at": utc_now(),
    }
    atomic_write(post_dir / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def is_post_done(post_dir: Path) -> bool:
    return (post_dir / "manifest.json").exists()


def image_exists(images_dir: Path, name: str) -> bool:
    return (images_dir / f"{name}.webp").exists()


# ---------------------------------------------------------------------------
# Delay helper
# ---------------------------------------------------------------------------

def _sleep(config: dict) -> None:
    d = config["delay_ms"] / 1000.0 + random.uniform(0, config["jitter_ms"] / 1000.0)
    if d > 0:
        time.sleep(d)


# ---------------------------------------------------------------------------
# Per-post processor
# ---------------------------------------------------------------------------

def process_post(slug: str, md_path: Path, config: dict) -> bool:
    log(f"PROCESSING: {slug}")

    post_dir   = config["output_dir"] / slug
    images_dir = post_dir / "images"

    # Read source
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception as e:
        log(f"  ERROR: could not read {md_path}: {e}")
        return False

    parsed  = parse_markdown(content)
    prompts = generate_prompts(parsed)

    if not parsed["title"]:
        log(f"  WARN: no H1 title found in {slug}")

    # Prepare output dirs
    post_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Write prompts.json (always refresh — no AI cost, useful for inspection)
    atomic_write(post_dir / "prompts.json", json.dumps(prompts, indent=2, ensure_ascii=False))

    mode = "ai" if config["use_image_ai"] else "placeholder"
    image_records: list[dict] = []

    # --- Featured image ---
    if image_exists(images_dir, "featured"):
        log("  SKIP: featured (exists)")
    else:
        try:
            img_mode = generate_image("featured", prompts["featured"], images_dir, config)
            log(f"  GENERATED: featured ({img_mode})")
            _sleep(config)
        except Exception as e:
            log(f"  ERROR: featured — {e}")
            if not config["continue_on_error"]:
                return False
            atomic_write_bytes(images_dir / "featured.webp", _placeholder_svg("featured"))

    image_records.append({"name": "featured", "type": "featured"})

    # --- Supporting images ---
    for img_spec in prompts["images"]:
        name = img_spec["name"]
        if image_exists(images_dir, name):
            log(f"  SKIP: {name} (exists)")
        else:
            try:
                img_mode = generate_image(name, img_spec["prompt"], images_dir, config)
                log(f"  GENERATED: {name} ({img_mode})")
                _sleep(config)
            except Exception as e:
                log(f"  ERROR: {name} — {e}")
                if not config["continue_on_error"]:
                    return False
                atomic_write_bytes(images_dir / f"{name}.webp", _placeholder_svg(name))

        image_records.append({
            "name":    name,
            "section": img_spec["section"],
            "type":    "diagram",
        })

    # --- Embed into Markdown ---
    updated = embed_images(content, parsed, prompts)
    atomic_write(post_dir / "article.md", updated)

    # --- Manifest (marks post as complete) ---
    write_manifest(post_dir, slug, parsed, image_records, mode)

    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    config = get_config()
    input_dir  = config["input_dir"]
    output_dir = config["output_dir"]

    if not input_dir.exists():
        log(f"ERROR: input dir not found: {input_dir}")
        sys.exit(1)

    posts = discover_posts(input_dir)
    if not posts:
        log(f"ERROR: no posts found in {input_dir}")
        sys.exit(1)

    log(f"Found {len(posts)} post(s) — mode: {'ai' if config['use_image_ai'] else 'placeholder'}")
    output_dir.mkdir(parents=True, exist_ok=True)

    success = failed = skipped = 0

    for slug, md_path in posts:
        post_dir = output_dir / slug
        if is_post_done(post_dir):
            log(f"SKIP: {slug} (already complete)")
            skipped += 1
            continue

        ok = process_post(slug, md_path, config)
        if ok:
            success += 1
        else:
            failed += 1
            if not config["continue_on_error"]:
                log("ERROR [ABORT]: continue_on_error=false. Stopping.")
                break

    log(f"\nDone. total={len(posts)} success={success} failed={failed} skipped={skipped}")


if __name__ == "__main__":
    run()
