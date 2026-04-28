from pipelines.guided_fix.main import (
    CostTracker,
    _impact_for,
    append_work_log,
    build_items,
    load_completed,
)


# ---------------------------------------------------------------------------
# _impact_for
# ---------------------------------------------------------------------------

def test_impact_known_critical():
    assert _impact_for("network_error") == 5


def test_impact_known_high():
    assert _impact_for("canonical_cross_language") == 4
    assert _impact_for("orphan_page") == 4


def test_impact_known_low():
    assert _impact_for("images_missing_alt") == 1


def test_impact_http_5xx_is_critical():
    assert _impact_for("http_500") == 5
    assert _impact_for("http_503") == 5


def test_impact_http_4xx_is_high():
    assert _impact_for("http_404") == 4
    assert _impact_for("http_410") == 4


def test_impact_unknown_default_medium():
    assert _impact_for("foo_bar_baz") == 3


# ---------------------------------------------------------------------------
# build_items
# ---------------------------------------------------------------------------

def test_build_items_groups_audit_technical_by_type():
    inputs = {
        "audit_technical": {
            "issues": [
                {"url": "https://x/a/", "type": "missing_title", "detail": ""},
                {"url": "https://x/b/", "type": "missing_title", "detail": ""},
                {"url": "https://x/c/", "type": "thin_meta_description", "detail": ""},
            ],
        },
        "audit_content": None,
    }
    items = build_items(inputs)
    titles = [i["slug"] for i in items]
    assert "missing_title" in titles
    assert "thin_meta_description" in titles
    mt = next(i for i in items if i["slug"] == "missing_title")
    assert mt["urls"] == ["https://x/a/", "https://x/b/"]


def test_build_items_includes_thin_pages_and_clusters():
    inputs = {
        "audit_technical": None,
        "audit_content": {
            "thin_pages": [
                {"url": "https://x/a/", "word_count": 100},
                {"url": "https://x/b/", "word_count": 200},
            ],
            "duplicate_clusters": [
                {"members": ["https://x/c/", "https://x/d/"], "max_similarity": 0.95},
            ],
        },
    }
    items = build_items(inputs)
    slugs = {i["slug"] for i in items}
    assert "thin_page" in slugs
    assert "duplicate_cluster_1" in slugs


def test_build_items_sorted_by_impact_desc():
    inputs = {
        "audit_technical": {
            "issues": [
                {"url": "https://x/a/", "type": "images_missing_alt", "detail": ""},  # impact 1
                {"url": "https://x/b/", "type": "canonical_cross_language", "detail": ""},  # impact 4
                {"url": "https://x/c/", "type": "missing_canonical", "detail": ""},  # impact 3
            ],
        },
        "audit_content": None,
    }
    items = build_items(inputs)
    impacts = [i["impact"] for i in items]
    assert impacts == sorted(impacts, reverse=True)
    assert items[0]["slug"] == "canonical_cross_language"
    assert items[-1]["slug"] == "images_missing_alt"


def test_build_items_dedupes_urls_within_type():
    inputs = {
        "audit_technical": {
            "issues": [
                {"url": "https://x/a/", "type": "missing_title", "detail": ""},
                {"url": "https://x/a/", "type": "missing_title", "detail": ""},
            ],
        },
        "audit_content": None,
    }
    items = build_items(inputs)
    assert items[0]["urls"] == ["https://x/a/"]


# ---------------------------------------------------------------------------
# work-log
# ---------------------------------------------------------------------------

def test_load_completed_missing_returns_empty(tmp_path):
    assert load_completed(tmp_path / "missing.md") == set()


def test_append_and_load_completed(tmp_path):
    log_path = tmp_path / "work-log.md"
    item = {"slug": "canonical_cross_language", "title": "Canonical fix"}
    append_work_log(log_path, item, status="done", cost_usd=0.34)
    append_work_log(log_path, item, status="done", cost_usd=0.10)  # idempotent record
    other = {"slug": "thin_page", "title": "Thin pages"}
    append_work_log(log_path, other, status="skipped")

    done = load_completed(log_path)
    assert done == {"canonical_cross_language"}
    # Skipped doesn't count as completed
    assert "thin_page" not in done


def test_append_writes_header_first(tmp_path):
    log_path = tmp_path / "work-log.md"
    append_work_log(log_path, {"slug": "x", "title": "y"}, status="done")
    text = log_path.read_text()
    assert text.startswith("# Work Log")


# ---------------------------------------------------------------------------
# CostTracker
# ---------------------------------------------------------------------------

def test_cost_tracker_starts_zero():
    c = CostTracker(max_session=5.0, input_price=3.0, output_price=15.0)
    assert c.total == 0.0
    assert c.calls == 0


def test_cost_tracker_input_pricing():
    c = CostTracker(max_session=5.0, input_price=3.0, output_price=15.0)
    c.add(input_tokens=1_000_000, output_tokens=0)
    assert c.total == 3.0


def test_cost_tracker_output_pricing():
    c = CostTracker(max_session=5.0, input_price=3.0, output_price=15.0)
    c.add(input_tokens=0, output_tokens=1_000_000)
    assert c.total == 15.0


def test_cost_tracker_session_cap():
    c = CostTracker(max_session=1.0, input_price=3.0, output_price=15.0)
    assert not c.session_exceeded()
    c.add(input_tokens=400_000, output_tokens=0)  # $1.20
    assert c.session_exceeded()


def test_cost_tracker_call_counter():
    c = CostTracker(max_session=5.0, input_price=3.0, output_price=15.0)
    c.add(100, 50)
    c.add(200, 100)
    assert c.calls == 2
    assert c.input_tokens == 300
    assert c.output_tokens == 150
