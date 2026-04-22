#!/usr/bin/env python3
"""
SEO Image Embedder
Reads Markdown posts with existing images and embeds them as Markdown image tags.
Does NOT generate images — images must already exist in the input images/ directory.

Input layouts supported (auto-detected):
  input/<slug>.md                         — flat file (no images, copied as-is)
  input/<slug>/article.md + images/       — folder with images
  input/posts/<slug>.md                   — same as above under posts/ subdir
  input/posts/<slug>/article.md + images/

Output always written to:
  output/posts/<slug>/article.md
  output/posts/<slug>/images/
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.env import load_env_file
from lib.io import atomic_write, log, utc_now

# Image file extensions recognised as embeddable
_IMG_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".svg", ".gif"}

# Sections whose H2 headings are too generic to map a diagram to
_SKIP_SECTIONS = frozenset({
    "introduction",
    "conclusion",
    "quick answer",
    "frequently asked questions",
    "related resources",
    "faq",
})


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def get_config() -> dict:
    load_env_file("../../seo.env", "embed.env")
    return {
        "input_dir":        Path(os.environ.get("INPUT_DIR", "input")),
        "output_dir":       Path(os.environ.get("OUTPUT_DIR", "output/posts")),
        "continue_on_error": os.environ.get("CONTINUE_ON_ERROR", "true").lower() == "true",
    }


# ---------------------------------------------------------------------------
# Input discovery
# ---------------------------------------------------------------------------

def _scan_dir(directory: Path) -> list[tuple[str, Path, Path | None]]:
    """
    Scan one directory level.
    Returns [(slug, md_path, images_dir_or_None), ...].
    """
    results: list[tuple[str, Path, Path | None]] = []
    for item in sorted(directory.iterdir()):
        if item.is_file() and item.suffix == ".md":
            results.append((item.stem, item, None))
        elif item.is_dir() and item.name not in ("posts", "output"):
            article = item / "article.md"
            if article.exists():
                images_dir = item / "images"
                results.append((item.name, article, images_dir if images_dir.is_dir() else None))
    return results


def discover_posts(input_dir: Path) -> list[tuple[str, Path, Path | None]]:
    """
    Return [(slug, md_path, images_dir_or_None), ...] from input_dir.
    Also scans input_dir/posts/ if it exists.
    """
    if not input_dir.exists():
        return []

    found: list[tuple[str, Path, Path | None]] = []
    seen: set[str] = set()

    for slug, md, imgs in _scan_dir(input_dir):
        if slug not in seen:
            found.append((slug, md, imgs))
            seen.add(slug)

    posts_sub = input_dir / "posts"
    if posts_sub.is_dir():
        for slug, md, imgs in _scan_dir(posts_sub):
            if slug not in seen:
                found.append((slug, md, imgs))
                seen.add(slug)

    return sorted(found, key=lambda t: t[0])


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------

def parse_markdown(content: str) -> dict:
    """Extract title, keyword, topic, and H2 section headings."""
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
        "title":       title,
        "keyword":     keyword,
        "topic":       keyword or title,
        "h2_sections": h2_sections,
    }


# ---------------------------------------------------------------------------
# Image discovery
# ---------------------------------------------------------------------------

def discover_images(images_dir: Path) -> tuple[Path | None, list[Path]]:
    """
    Scan images_dir and return (featured_path, [supporting_path, ...]).
    featured.* → featured; everything else → supporting, sorted by name.
    """
    if not images_dir or not images_dir.is_dir():
        return None, []

    featured: Path | None = None
    supporting: list[Path] = []

    for p in sorted(images_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in _IMG_EXTENSIONS:
            if p.stem.lower() == "featured":
                featured = p
            else:
                supporting.append(p)

    return featured, supporting


# ---------------------------------------------------------------------------
# Section map (optional — loaded from prompts.json if present)
# ---------------------------------------------------------------------------

def load_section_map(post_input_dir: Path) -> dict[str, str]:
    """
    Load {image_name: section_heading} from prompts.json if present.
    Returns empty dict if not found or unparseable.
    """
    prompts_path = post_input_dir / "prompts.json"
    if not prompts_path.exists():
        return {}
    try:
        data = json.loads(prompts_path.read_text(encoding="utf-8"))
        return {img["name"]: img["section"] for img in data.get("images", []) if "name" in img and "section" in img}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Detect already-embedded images
# ---------------------------------------------------------------------------

_IMG_TAG_RE = re.compile(r"!\[.*?\]\(images/([^)]+)\)")


def detect_embedded(content: str) -> set[str]:
    """Return stems of images already embedded (e.g. {'featured', 'diagram-1'})."""
    embedded: set[str] = set()
    for match in _IMG_TAG_RE.finditer(content):
        stem = Path(match.group(1)).stem
        embedded.add(stem)
    return embedded


# ---------------------------------------------------------------------------
# Alt text generation
# ---------------------------------------------------------------------------

def _alt_for_featured(parsed: dict) -> str:
    title   = parsed["title"]
    keyword = parsed["keyword"] or parsed["topic"]
    return f"{title} — {keyword} technical overview diagram"


def _alt_for_supporting(image_path: Path, section: str, parsed: dict) -> str:
    keyword = parsed["keyword"] or parsed["topic"]
    if section:
        return f"{section} — {keyword} diagram"
    # Fall back to a cleaned-up image stem
    label = image_path.stem.replace("-", " ").replace("_", " ").title()
    return f"{label} — {keyword}"


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def _img_tag(rel_path: str, alt: str) -> str:
    return f"![{alt}]({rel_path})"


def embed_images(
    content:     str,
    parsed:      dict,
    featured:    Path | None,
    supporting:  list[Path],
    section_map: dict[str, str],
    already_embedded: set[str],
) -> tuple[str, list[str]]:
    """
    Insert image tags into content.
    Returns (updated_content, [log_messages]).
    Only embeds images not already present.
    Max one supporting image per H2 section.
    """
    logs: list[str] = []

    # Filter to images not yet embedded
    to_embed_featured = (
        featured if featured and featured.stem not in already_embedded else None
    )
    to_embed_supporting = [
        p for p in supporting if p.stem not in already_embedded
    ]

    if to_embed_featured is None and featured:
        logs.append(f"  SKIPPED: {featured.name} (already embedded)")
    for p in supporting:
        if p.stem in already_embedded:
            logs.append(f"  SKIPPED: {p.name} (already embedded)")

    if not to_embed_featured and not to_embed_supporting:
        return content, logs

    lines = content.splitlines()
    result: list[str] = []

    featured_done = False
    remaining_supporting = list(to_embed_supporting)
    placed: set[str] = set()

    def insert(rel: str, alt: str) -> None:
        result.append("")
        result.append(_img_tag(rel, alt))
        result.append("")

    for line in lines:
        result.append(line)

        # Featured: immediately after H1
        if not featured_done and to_embed_featured and re.match(r"^# (?!#)", line):
            rel = f"images/{to_embed_featured.name}"
            insert(rel, _alt_for_featured(parsed))
            logs.append(f"  EMBEDDED: {to_embed_featured.name} after H1")
            featured_done = True
            continue

        # Supporting: after matching H2
        if remaining_supporting and re.match(r"^## (?!#)", line):
            section_name = line[3:].strip()
            section_lower = section_name.lower()

            if section_lower in _SKIP_SECTIONS:
                continue

            for img_path in remaining_supporting:
                if img_path.stem in placed:
                    continue
                target_section = section_map.get(img_path.stem, "").lower()

                matched = False
                if target_section:
                    # Prompts.json section match
                    matched = target_section in section_lower or section_lower in target_section
                else:
                    # No section map — any non-skip section claims the next image
                    matched = True

                if matched:
                    rel = f"images/{img_path.name}"
                    alt = _alt_for_supporting(img_path, section_map.get(img_path.stem, section_name), parsed)
                    insert(rel, alt)
                    logs.append(f"  EMBEDDED: {img_path.name} after H2 \"{section_name}\"")
                    placed.add(img_path.stem)
                    break  # one image per section

    # Evenly distribute any remaining unplaced supporting images
    still_remaining = [p for p in remaining_supporting if p.stem not in placed]
    if still_remaining:
        h2_positions = [
            i for i, ln in enumerate(result)
            if re.match(r"^## (?!#)", ln) and ln[3:].strip().lower() not in _SKIP_SECTIONS
        ]

        if h2_positions:
            # Spread evenly across available H2 positions
            step = max(1, len(h2_positions) // (len(still_remaining) + 1))
            targets = [
                h2_positions[min(i * step, len(h2_positions) - 1)]
                for i in range(1, len(still_remaining) + 1)
            ]

            for img_path, idx in zip(still_remaining, sorted(targets, reverse=True)):
                rel = f"images/{img_path.name}"
                section_label = result[idx][3:].strip() if idx < len(result) else ""
                alt = _alt_for_supporting(img_path, section_label, parsed)
                result.insert(idx + 1, "")
                result.insert(idx + 2, _img_tag(rel, alt))
                result.insert(idx + 3, "")
                logs.append(f"  EMBEDDED: {img_path.name} (evenly spaced)")
        else:
            # No usable H2s at all — append at end
            for img_path in still_remaining:
                rel = f"images/{img_path.name}"
                alt = _alt_for_supporting(img_path, "", parsed)
                result.append("")
                result.append(_img_tag(rel, alt))
                logs.append(f"  EMBEDDED: {img_path.name} (appended at end)")

    return "\n".join(result), logs


def write_manifest(post_dir: Path, slug: str, parsed: dict, embedded: list[str]) -> None:
    manifest = {
        "slug":         slug,
        "title":        parsed["title"],
        "keyword":      parsed["keyword"],
        "embedded":     embedded,
        "generated_at": utc_now(),
    }
    atomic_write(post_dir / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def is_post_done(post_dir: Path) -> bool:
    return (post_dir / "manifest.json").exists()


# ---------------------------------------------------------------------------
# Per-post processor
# ---------------------------------------------------------------------------

def process_post(
    slug:       str,
    md_path:    Path,
    images_dir: Path | None,
    config:     dict,
) -> bool:
    log(f"PROCESSING: {slug}")

    output_dir  = config["output_dir"]
    post_out    = output_dir / slug
    images_out  = post_out / "images"

    # Read article
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception as e:
        log(f"  ERROR: cannot read {md_path}: {e}")
        return False

    parsed = parse_markdown(content)

    # Discover images
    featured, supporting = discover_images(images_dir)

    if not featured and not supporting:
        log(f"  WARN: no images found — copying article unchanged")
        post_out.mkdir(parents=True, exist_ok=True)
        atomic_write(post_out / "article.md", content)
        write_manifest(post_out, slug, parsed, [])
        return True

    log(f"  Found: {'featured + ' if featured else ''}{len(supporting)} supporting image(s)")

    # Optional section map from prompts.json (produced by generate_images stage)
    section_map = load_section_map(images_dir.parent) if images_dir else {}

    # Detect images already embedded in the source
    already_embedded = detect_embedded(content)

    # Embed
    updated_content, embed_logs = embed_images(
        content, parsed, featured, supporting, section_map, already_embedded
    )
    for msg in embed_logs:
        log(msg)

    embedded_names = [
        p.name for p in ([featured] if featured else []) + supporting
        if p.stem not in already_embedded
    ]

    # Write article.md
    post_out.mkdir(parents=True, exist_ok=True)
    atomic_write(post_out / "article.md", updated_content)

    # Copy images to output (skip if src == dst)
    if images_dir and images_dir.resolve() != images_out.resolve():
        images_out.mkdir(parents=True, exist_ok=True)
        for img in ([featured] if featured else []) + supporting:
            dst = images_out / img.name
            try:
                shutil.copy2(img, dst)
                os.chmod(dst, 0o666)
            except Exception as e:
                log(f"  ERROR: could not copy {img.name}: {e}")

    write_manifest(post_out, slug, parsed, embedded_names)
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    config    = get_config()
    input_dir = config["input_dir"]
    output_dir = config["output_dir"]

    if not input_dir.exists():
        log(f"ERROR: input dir not found: {input_dir}")
        sys.exit(1)

    posts = discover_posts(input_dir)
    if not posts:
        log(f"ERROR: no posts found in {input_dir}")
        sys.exit(1)

    log(f"Found {len(posts)} post(s)")
    output_dir.mkdir(parents=True, exist_ok=True)

    success = failed = skipped = 0

    for slug, md_path, images_dir in posts:
        post_out = output_dir / slug
        if is_post_done(post_out):
            log(f"SKIP: {slug} (already complete)")
            skipped += 1
            continue

        try:
            ok = process_post(slug, md_path, images_dir, config)
        except Exception as e:
            log(f"ERROR: {slug} — {type(e).__name__}: {e}")
            ok = False

        if ok:
            success += 1
        else:
            failed += 1
            if not config["continue_on_error"]:
                log("ERROR [ABORT]: CONTINUE_ON_ERROR=false. Stopping.")
                break

    log(f"\nDone. total={len(posts)} success={success} failed={failed} skipped={skipped}")


if __name__ == "__main__":
    run()
