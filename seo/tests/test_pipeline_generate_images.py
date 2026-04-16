import pytest
from pathlib import Path
from pipelines.generate_images.main import (
    _pick_supporting_h2s,
    _placeholder_svg,
    embed_images,
    parse_markdown,
)

SAMPLE_ARTICLE = """\
# Hybrid Battery Guide

**Primary keyword:** hybrid battery replacement

## What Is a Hybrid Battery

Content here.

## How to Replace a Hybrid Battery

More content.

## Cost of Replacement

Costs.

## Conclusion

Final words.
"""


# ---------------------------------------------------------------------------
# parse_markdown
# ---------------------------------------------------------------------------

def test_parse_markdown_extracts_title():
    parsed = parse_markdown(SAMPLE_ARTICLE)
    assert parsed["title"] == "Hybrid Battery Guide"


def test_parse_markdown_extracts_keyword():
    parsed = parse_markdown(SAMPLE_ARTICLE)
    assert parsed["keyword"] == "hybrid battery replacement"


def test_parse_markdown_topic_is_keyword_when_present():
    parsed = parse_markdown(SAMPLE_ARTICLE)
    assert parsed["topic"] == "hybrid battery replacement"


def test_parse_markdown_topic_falls_back_to_title():
    content = "# My Title\n\n## Section One\n"
    parsed = parse_markdown(content)
    assert parsed["topic"] == "My Title"


def test_parse_markdown_extracts_h2_sections():
    parsed = parse_markdown(SAMPLE_ARTICLE)
    assert "What Is a Hybrid Battery" in parsed["h2_sections"]
    assert "How to Replace a Hybrid Battery" in parsed["h2_sections"]


def test_parse_markdown_no_h1_title_is_empty():
    content = "## Just a section\n"
    assert parse_markdown(content)["title"] == ""


def test_parse_markdown_ignores_h3_in_h2_list():
    content = "# Title\n### Not H2\n## Real H2\n"
    h2s = parse_markdown(content)["h2_sections"]
    assert "Real H2" in h2s
    assert "Not H2" not in h2s


# ---------------------------------------------------------------------------
# _pick_supporting_h2s
# ---------------------------------------------------------------------------

def test_pick_supporting_h2s_filters_skip_sections():
    h2s = ["Introduction", "How It Works", "Conclusion", "Best Practices"]
    picked = _pick_supporting_h2s(h2s)
    assert "Introduction" not in picked
    assert "Conclusion" not in picked
    assert "How It Works" in picked


def test_pick_supporting_h2s_respects_max_count():
    h2s = ["A", "B", "C", "D", "E"]
    picked = _pick_supporting_h2s(h2s, max_count=3)
    assert len(picked) <= 3


def test_pick_supporting_h2s_fallback_to_all_when_few_content_sections():
    # If filtering leaves fewer than min_count, fall back to all
    h2s = ["Introduction", "Conclusion"]
    picked = _pick_supporting_h2s(h2s, min_count=2)
    assert len(picked) >= 1


# ---------------------------------------------------------------------------
# _placeholder_svg
# ---------------------------------------------------------------------------

def test_placeholder_svg_returns_bytes():
    result = _placeholder_svg("featured")
    assert isinstance(result, bytes)


def test_placeholder_svg_contains_label():
    result = _placeholder_svg("my-label")
    assert b"my-label" in result


def test_placeholder_svg_is_valid_xml():
    result = _placeholder_svg("test")
    assert result.startswith(b"<?xml")
    assert b"<svg" in result


def test_placeholder_svg_escapes_special_chars():
    result = _placeholder_svg("a&b<c>d")
    assert b"a&amp;b&lt;c&gt;d" in result


# ---------------------------------------------------------------------------
# embed_images
# ---------------------------------------------------------------------------

def _make_prompts(sections: list[str]) -> dict:
    return {
        "featured": "featured prompt",
        "images": [
            {"name": f"diagram-{i+1}", "section": s, "prompt": f"prompt {s}"}
            for i, s in enumerate(sections)
        ],
    }


def test_embed_images_featured_after_h1():
    parsed = parse_markdown(SAMPLE_ARTICLE)
    prompts = _make_prompts(["How to Replace a Hybrid Battery"])
    result = embed_images(SAMPLE_ARTICLE, parsed, prompts)
    lines = result.splitlines()
    h1_idx = next(i for i, l in enumerate(lines) if l.startswith("# "))
    img_lines = [l for l in lines[h1_idx:h1_idx+4] if "featured" in l]
    assert img_lines, "featured image tag not found after H1"


def test_embed_images_supporting_after_h2():
    parsed = parse_markdown(SAMPLE_ARTICLE)
    prompts = _make_prompts(["How to Replace a Hybrid Battery"])
    result = embed_images(SAMPLE_ARTICLE, parsed, prompts)
    lines = result.splitlines()

    # Find the H2 index
    h2_idx = next(i for i, l in enumerate(lines) if "How to Replace" in l)
    # diagram-1 should appear shortly after
    nearby = "\n".join(lines[h2_idx:h2_idx+5])
    assert "diagram-1" in nearby


def test_embed_images_unmatched_are_placed():
    parsed = parse_markdown(SAMPLE_ARTICLE)
    # Use a section that doesn't exist in the article
    prompts = _make_prompts(["Nonexistent Section Name"])
    result = embed_images(SAMPLE_ARTICLE, parsed, prompts)
    # Image should still appear somewhere
    assert "diagram-1" in result
