import pytest
from pathlib import Path
from pipelines.embed_images.main import (
    _alt_for_featured,
    _alt_for_supporting,
    detect_embedded,
    discover_images,
    embed_images,
    parse_markdown,
)

SAMPLE_ARTICLE = """\
# Hybrid Battery Guide

**Primary keyword:** hybrid battery

## What Is a Hybrid Battery

Content here.

## How to Replace It

Step-by-step.

## Conclusion

Done.
"""


# ---------------------------------------------------------------------------
# parse_markdown
# ---------------------------------------------------------------------------

def test_parse_markdown_title():
    assert parse_markdown(SAMPLE_ARTICLE)["title"] == "Hybrid Battery Guide"


def test_parse_markdown_keyword():
    assert parse_markdown(SAMPLE_ARTICLE)["keyword"] == "hybrid battery"


def test_parse_markdown_h2_sections():
    h2s = parse_markdown(SAMPLE_ARTICLE)["h2_sections"]
    assert "What Is a Hybrid Battery" in h2s
    assert "How to Replace It" in h2s


def test_parse_markdown_no_keyword_topic_is_title():
    content = "# Just Title\n\n## Section\n"
    parsed = parse_markdown(content)
    assert parsed["topic"] == "Just Title"


# ---------------------------------------------------------------------------
# discover_images
# ---------------------------------------------------------------------------

def test_discover_images_featured_and_supporting(tmp_path):
    (tmp_path / "featured.webp").write_bytes(b"img")
    (tmp_path / "diagram-1.webp").write_bytes(b"img")
    (tmp_path / "diagram-2.webp").write_bytes(b"img")
    featured, supporting = discover_images(tmp_path)
    assert featured is not None
    assert featured.stem == "featured"
    assert len(supporting) == 2


def test_discover_images_no_featured(tmp_path):
    (tmp_path / "diagram-1.webp").write_bytes(b"img")
    featured, supporting = discover_images(tmp_path)
    assert featured is None
    assert len(supporting) == 1


def test_discover_images_missing_dir():
    featured, supporting = discover_images(Path("/nonexistent/dir"))
    assert featured is None
    assert supporting == []


def test_discover_images_only_recognised_extensions(tmp_path):
    (tmp_path / "featured.webp").write_bytes(b"img")
    (tmp_path / "notes.txt").write_text("not an image")
    _, supporting = discover_images(tmp_path)
    assert all(p.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg", ".svg", ".gif"} for p in supporting)


# ---------------------------------------------------------------------------
# detect_embedded
# ---------------------------------------------------------------------------

def test_detect_embedded_finds_stems():
    content = "![alt](images/featured.webp)\n![alt](images/diagram-1.webp)"
    assert detect_embedded(content) == {"featured", "diagram-1"}


def test_detect_embedded_empty_when_none():
    assert detect_embedded("No images here.") == set()


def test_detect_embedded_ignores_external_images():
    content = "![alt](https://example.com/image.png)"
    assert detect_embedded(content) == set()


# ---------------------------------------------------------------------------
# alt text helpers
# ---------------------------------------------------------------------------

def test_alt_for_featured():
    parsed = {"title": "Hybrid Battery Guide", "keyword": "hybrid battery", "topic": "hybrid battery"}
    alt = _alt_for_featured(parsed)
    assert "Hybrid Battery Guide" in alt
    assert "hybrid battery" in alt


def test_alt_for_supporting_with_section(tmp_path):
    img = tmp_path / "diagram-1.webp"
    img.write_bytes(b"x")
    parsed = {"keyword": "hybrid battery", "topic": "hybrid battery", "title": ""}
    alt = _alt_for_supporting(img, "Battery Chemistry", parsed)
    assert "Battery Chemistry" in alt
    assert "hybrid battery" in alt


def test_alt_for_supporting_no_section_uses_stem(tmp_path):
    img = tmp_path / "diagram-one.webp"
    img.write_bytes(b"x")
    parsed = {"keyword": "hybrid battery", "topic": "hybrid battery", "title": ""}
    alt = _alt_for_supporting(img, "", parsed)
    assert "hybrid battery" in alt
    assert "Diagram One" in alt


# ---------------------------------------------------------------------------
# embed_images
# ---------------------------------------------------------------------------

def _make_image(directory: Path, name: str) -> Path:
    p = directory / name
    p.write_bytes(b"img")
    return p


def test_embed_images_featured_after_h1(tmp_path):
    featured = _make_image(tmp_path, "featured.webp")
    parsed = parse_markdown(SAMPLE_ARTICLE)
    result, logs = embed_images(SAMPLE_ARTICLE, parsed, featured, [], {}, set())
    lines = result.splitlines()
    h1_idx = next(i for i, l in enumerate(lines) if l.startswith("# "))
    nearby = "\n".join(lines[h1_idx: h1_idx + 5])
    assert "featured.webp" in nearby


def test_embed_images_supporting_after_matching_h2(tmp_path):
    featured = _make_image(tmp_path, "featured.webp")
    diag = _make_image(tmp_path, "diagram-1.webp")
    parsed = parse_markdown(SAMPLE_ARTICLE)
    section_map = {"diagram-1": "What Is a Hybrid Battery"}
    result, logs = embed_images(SAMPLE_ARTICLE, parsed, featured, [diag], section_map, set())

    lines = result.splitlines()
    h2_idx = next(i for i, l in enumerate(lines) if "What Is a Hybrid Battery" in l)
    nearby = "\n".join(lines[h2_idx: h2_idx + 6])
    assert "diagram-1.webp" in nearby


def test_embed_images_skips_already_embedded(tmp_path):
    featured = _make_image(tmp_path, "featured.webp")
    parsed = parse_markdown(SAMPLE_ARTICLE)
    already = {"featured"}
    result, logs = embed_images(SAMPLE_ARTICLE, parsed, featured, [], {}, already)
    # featured should not appear a second time
    assert result.count("featured.webp") == 0


def test_embed_images_unmatched_supporting_placed_evenly(tmp_path):
    featured = _make_image(tmp_path, "featured.webp")
    diag = _make_image(tmp_path, "diagram-1.webp")
    parsed = parse_markdown(SAMPLE_ARTICLE)
    # No section_map → will fall back to even placement
    result, logs = embed_images(SAMPLE_ARTICLE, parsed, featured, [diag], {}, set())
    assert "diagram-1.webp" in result


def test_embed_images_returns_logs(tmp_path):
    featured = _make_image(tmp_path, "featured.webp")
    parsed = parse_markdown(SAMPLE_ARTICLE)
    _, logs = embed_images(SAMPLE_ARTICLE, parsed, featured, [], {}, set())
    assert any("featured" in l for l in logs)
