import json
import pytest
from pathlib import Path
from pipelines.write_articles.main import normalize_topic, parse_input


# ---------------------------------------------------------------------------
# normalize_topic
# ---------------------------------------------------------------------------

def test_normalize_topic_uses_primary_keyword():
    raw = {"primary_keyword": "hybrid battery replacement", "id": 1}
    t = normalize_topic(raw, 0)
    assert t["keyword"] == "hybrid battery replacement"


def test_normalize_topic_falls_back_to_keyword_field():
    raw = {"keyword": "hybrid oil change"}
    t = normalize_topic(raw, 0)
    assert t["keyword"] == "hybrid oil change"


def test_normalize_topic_falls_back_to_title_for_keyword():
    raw = {"title": "Hybrid Coolant"}
    t = normalize_topic(raw, 0)
    assert t["keyword"] == "Hybrid Coolant"


def test_normalize_topic_generates_slug_from_title():
    raw = {"title": "Hybrid Battery Guide", "keyword": "hybrid battery guide"}
    t = normalize_topic(raw, 0)
    assert t["slug"] == "hybrid-battery-guide"


def test_normalize_topic_explicit_slug_honoured():
    raw = {"keyword": "hybrid battery", "slug": "my-custom-slug"}
    t = normalize_topic(raw, 0)
    assert t["slug"] == "my-custom-slug"


def test_normalize_topic_fallback_slug_from_index():
    raw = {}
    t = normalize_topic(raw, 4)
    assert t["slug"] == "post-5"


def test_normalize_topic_defaults():
    raw = {"keyword": "hybrid battery"}
    t = normalize_topic(raw, 0)
    assert t["search_intent"] == "Informational"
    assert t["priority"] == "Medium"
    assert t["target_word_count"] == 1200
    assert t["aeo_snippet_target"] is False
    assert t["suggested_internal_links"] == []


def test_normalize_topic_target_word_count_cast():
    raw = {"keyword": "hybrid", "target_word_count": "1500"}
    t = normalize_topic(raw, 0)
    assert t["target_word_count"] == 1500


def test_normalize_topic_aeo_snippet_target():
    raw = {"keyword": "hybrid", "aeo_snippet_target": True}
    t = normalize_topic(raw, 0)
    assert t["aeo_snippet_target"] is True


def test_normalize_topic_id_defaults_to_index_plus_1():
    raw = {"keyword": "test"}
    t = normalize_topic(raw, 2)
    assert t["id"] == 3


# ---------------------------------------------------------------------------
# parse_input
# ---------------------------------------------------------------------------

def test_parse_input_list_format(tmp_path):
    data = [{"keyword": "hybrid brake", "id": 1}]
    p = tmp_path / "topics.json"
    p.write_text(json.dumps(data))
    topics = parse_input(str(p))
    assert len(topics) == 1
    assert topics[0]["keyword"] == "hybrid brake"


def test_parse_input_posts_dict_format(tmp_path):
    data = {"posts": [{"keyword": "hybrid tire", "id": 1}]}
    p = tmp_path / "topics.json"
    p.write_text(json.dumps(data))
    topics = parse_input(str(p))
    assert len(topics) == 1
    assert topics[0]["keyword"] == "hybrid tire"


def test_parse_input_bad_format_raises(tmp_path):
    p = tmp_path / "topics.json"
    p.write_text(json.dumps({"unexpected": "structure"}))
    with pytest.raises(ValueError, match="Unrecognized"):
        parse_input(str(p))


def test_parse_input_empty_list(tmp_path):
    p = tmp_path / "topics.json"
    p.write_text("[]")
    assert parse_input(str(p)) == []
