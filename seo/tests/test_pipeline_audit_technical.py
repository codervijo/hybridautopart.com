from pipelines.audit_technical.main import (
    audit_pages,
    check_canonical_mismatch,
    check_cross_language_link,
    check_duplicates,
    check_h1_count,
    check_images_missing_alt,
    check_internal_link_count,
    check_meta_too_long,
    check_missing_canonical,
    check_missing_meta,
    check_missing_title,
    check_orphan_pages,
    check_outbound_link_count,
    check_redirect_chain,
    check_status,
    check_thin_meta,
    check_title_h1_mismatch,
    check_title_length,
    dedupe_by_url,
)


def _page(**overrides) -> dict:
    base = {
        "url": "https://hybridautopart.com/blog-en/x/",
        "final_url": "https://hybridautopart.com/blog-en/x/",
        "status": 200,
        "redirects": [],
        "title": "X",
        "meta_description": "A reasonable description that is at least 50 chars long, no problem.",
        "canonical": "https://hybridautopart.com/blog-en/x/",
        "h1": ["X"],
        "word_count": 1500,
        "internal_links": [],
        "outbound_links": [],
        "images_without_alt": 0,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# check_status
# ---------------------------------------------------------------------------

def test_status_ok_no_issue():
    assert check_status(_page(status=200)) == []


def test_status_404():
    out = check_status(_page(status=404))
    assert out[0]["type"] == "http_404"


def test_status_500():
    assert check_status(_page(status=500))[0]["type"] == "http_500"


def test_status_zero_is_network_error():
    out = check_status(_page(status=0, error="DNS lookup failed"))
    assert out[0]["type"] == "network_error"
    assert "DNS" in out[0]["detail"]


# ---------------------------------------------------------------------------
# check_redirect_chain
# ---------------------------------------------------------------------------

def test_redirect_single_hop_ok():
    p = _page(redirects=[{"from": "a", "to": "b", "status": 301}])
    assert check_redirect_chain(p) == []


def test_redirect_two_hops_flagged():
    p = _page(redirects=[
        {"from": "a", "to": "b", "status": 301},
        {"from": "b", "to": "c", "status": 301},
    ])
    out = check_redirect_chain(p)
    assert out[0]["type"] == "redirect_chain"
    assert "2 hops" in out[0]["detail"]


# ---------------------------------------------------------------------------
# title / meta / canonical
# ---------------------------------------------------------------------------

def test_missing_title_flagged():
    assert check_missing_title(_page(title=""))[0]["type"] == "missing_title"
    assert check_missing_title(_page(title="   "))[0]["type"] == "missing_title"


def test_missing_title_skipped_for_non_200():
    assert check_missing_title(_page(status=404, title="")) == []


def test_missing_meta_flagged():
    assert check_missing_meta(_page(meta_description=""))[0]["type"] == "missing_meta_description"


def test_thin_meta_flagged():
    out = check_thin_meta(_page(meta_description="Power split device"))
    assert out[0]["type"] == "thin_meta_description"
    assert "18 chars" in out[0]["detail"]


def test_thin_meta_not_flagged_when_empty():
    # Empty meta is `missing`, not `thin` — they're separate checks
    assert check_thin_meta(_page(meta_description="")) == []


def test_missing_canonical_flagged():
    assert check_missing_canonical(_page(canonical=""))[0]["type"] == "missing_canonical"


def test_canonical_different_path_flagged():
    # Same language space (no /xx/ prefix on either), different paths
    p = _page(
        final_url="https://hybridautopart.com/blog-en/x/",
        canonical="https://hybridautopart.com/blog-en/wrong/",
    )
    assert check_canonical_mismatch(p)[0]["type"] == "canonical_different_path"


def test_canonical_cross_language_flagged():
    # Source has no language prefix, canonical points to /fr/... — Polylang misconfig
    p = _page(
        final_url="https://hybridautopart.com/about-us/",
        canonical="https://hybridautopart.com/fr/about-us/",
    )
    assert check_canonical_mismatch(p)[0]["type"] == "canonical_cross_language"


def test_canonical_trailing_slash_tolerated():
    p = _page(
        final_url="https://hybridautopart.com/blog-en/x",
        canonical="https://hybridautopart.com/blog-en/x/",
    )
    assert check_canonical_mismatch(p) == []


# ---------------------------------------------------------------------------
# cross-language links
# ---------------------------------------------------------------------------

def test_cross_language_link_flagged():
    p = _page(internal_links=[
        "https://hybridautopart.com/blog-en/other/",      # OK
        "https://hybridautopart.com/blog/old-french-slug/",  # flagged
    ])
    out = check_cross_language_link(p)
    assert len(out) == 1
    assert out[0]["type"] == "cross_language_link"


def test_cross_language_link_blog_en_not_flagged():
    p = _page(internal_links=["https://hybridautopart.com/blog-en/anything/"])
    assert check_cross_language_link(p) == []


# ---------------------------------------------------------------------------
# duplicates
# ---------------------------------------------------------------------------

def test_duplicate_title_flagged_for_both():
    pages = [
        _page(url="https://x/a/", title="Same Title"),
        _page(url="https://x/b/", title="Same Title"),
        _page(url="https://x/c/", title="Different"),
    ]
    out = check_duplicates(pages, "title", "duplicate_title")
    flagged = {i["url"] for i in out}
    assert flagged == {"https://x/a/", "https://x/b/"}


def test_duplicate_meta_flagged():
    pages = [
        _page(url="https://x/a/", meta_description="Same meta description shared across pages."),
        _page(url="https://x/b/", meta_description="Same meta description shared across pages."),
    ]
    out = check_duplicates(pages, "meta_description", "duplicate_meta_description")
    assert len(out) == 2


def test_duplicates_ignore_non_200():
    pages = [
        _page(url="https://x/a/", title="Same"),
        _page(url="https://x/b/", title="Same", status=404),
    ]
    assert check_duplicates(pages, "title", "duplicate_title") == []


def test_duplicates_ignore_empty_field():
    pages = [
        _page(url="https://x/a/", title=""),
        _page(url="https://x/b/", title=""),
    ]
    assert check_duplicates(pages, "title", "duplicate_title") == []


# ---------------------------------------------------------------------------
# dedupe_by_url
# ---------------------------------------------------------------------------

def test_dedupe_by_url_first_wins():
    pages = [
        _page(url="https://x/a/", title="first"),
        _page(url="https://x/a/", title="second"),
        _page(url="https://x/b/", title="b"),
    ]
    out = dedupe_by_url(pages)
    assert len(out) == 2
    assert out[0]["title"] == "first"


def test_dedupe_by_url_preserves_order():
    pages = [
        _page(url="https://x/a/"),
        _page(url="https://x/b/"),
        _page(url="https://x/a/"),
        _page(url="https://x/c/"),
    ]
    assert [p["url"] for p in dedupe_by_url(pages)] == [
        "https://x/a/", "https://x/b/", "https://x/c/",
    ]


def test_audit_pages_does_not_flag_dupe_self_as_duplicate_title():
    # Without input dedup, two identical records would fire duplicate_title against
    # themselves. Regression test for the homepage-twice-in-sitemap quirk.
    pages = [
        _page(url="https://x/a/", title="Same"),
        _page(url="https://x/a/", title="Same"),
    ]
    types = {i["type"] for i in audit_pages(pages)}
    assert "duplicate_title" not in types


# ---------------------------------------------------------------------------
# title length
# ---------------------------------------------------------------------------

def test_title_too_short():
    assert check_title_length(_page(title="Short"))[0]["type"] == "title_too_short"


def test_title_too_long():
    long = "x" * 70
    assert check_title_length(_page(title=long))[0]["type"] == "title_too_long"


def test_title_in_range_ok():
    assert check_title_length(_page(title="A perfectly fine 40-character page title!")) == []


def test_title_length_skipped_when_empty():
    assert check_title_length(_page(title="")) == []


# ---------------------------------------------------------------------------
# meta length
# ---------------------------------------------------------------------------

def test_meta_too_long():
    long_meta = "x" * 200
    assert check_meta_too_long(_page(meta_description=long_meta))[0]["type"] == "meta_too_long"


def test_meta_in_range_ok():
    assert check_meta_too_long(_page()) == []


# ---------------------------------------------------------------------------
# H1
# ---------------------------------------------------------------------------

def test_missing_h1():
    assert check_h1_count(_page(h1=[]))[0]["type"] == "missing_h1"


def test_multiple_h1():
    out = check_h1_count(_page(h1=["A", "B"]))
    assert out[0]["type"] == "multiple_h1"


def test_single_h1_ok():
    assert check_h1_count(_page(h1=["X"])) == []


# ---------------------------------------------------------------------------
# title / H1 mismatch
# ---------------------------------------------------------------------------

def test_title_h1_match_no_issue():
    p = _page(title="Toyota Hybrid Synergy Drive Problems",
              h1=["Toyota Hybrid Synergy Drive Problems"])
    assert check_title_h1_mismatch(p) == []


def test_title_h1_mismatch_flagged():
    # The exact case from HAP_SEO_AUDIT.md: URL is about "problems" but H1 is an explainer
    p = _page(title="Toyota Hybrid Synergy Drive Problems",
              h1=["What Is Toyota Hybrid Synergy Drive? (Simple Explanation)"])
    out = check_title_h1_mismatch(p)
    assert out[0]["type"] == "title_h1_mismatch"
    assert "overlap=" in out[0]["detail"]


def test_title_h1_mismatch_skipped_when_h1_missing():
    assert check_title_h1_mismatch(_page(h1=[])) == []


# ---------------------------------------------------------------------------
# internal / outbound link counts
# ---------------------------------------------------------------------------

def test_few_internal_links_flagged():
    p = _page(internal_links=["https://x/a/", "https://x/b/"])
    assert check_internal_link_count(p)[0]["type"] == "few_internal_links"


def test_three_internal_links_ok():
    p = _page(internal_links=["https://x/a/", "https://x/b/", "https://x/c/"])
    assert check_internal_link_count(p) == []


def test_many_outbound_links_flagged():
    p = _page(outbound_links=[f"https://other.com/{i}" for i in range(25)])
    assert check_outbound_link_count(p)[0]["type"] == "many_outbound_links"


def test_outbound_under_threshold_ok():
    p = _page(outbound_links=[f"https://other.com/{i}" for i in range(20)])
    assert check_outbound_link_count(p) == []


# ---------------------------------------------------------------------------
# images_missing_alt
# ---------------------------------------------------------------------------

def test_images_missing_alt_flagged():
    out = check_images_missing_alt(_page(images_without_alt=3))
    assert out[0]["type"] == "images_missing_alt"
    assert "3 image" in out[0]["detail"]


def test_images_with_alt_ok():
    assert check_images_missing_alt(_page(images_without_alt=0)) == []


# ---------------------------------------------------------------------------
# orphan pages
# ---------------------------------------------------------------------------

def test_orphan_page_flagged():
    pages = [
        _page(url="https://x/a/", internal_links=["https://x/b/"]),
        _page(url="https://x/b/", internal_links=["https://x/a/"]),
        _page(url="https://x/orphan/", internal_links=[]),
    ]
    flagged = {i["url"] for i in check_orphan_pages(pages) if i["type"] == "orphan_page"}
    assert flagged == {"https://x/orphan/"}


def test_self_links_dont_count_as_inbound():
    pages = [
        _page(url="https://x/a/", internal_links=["https://x/a/"]),
    ]
    flagged = {i["url"] for i in check_orphan_pages(pages) if i["type"] == "orphan_page"}
    assert flagged == {"https://x/a/"}


def test_orphan_ignores_query_and_fragment():
    pages = [
        _page(url="https://x/a/", internal_links=["https://x/b/?ref=top#section"]),
        _page(url="https://x/b/", internal_links=["https://x/a/"]),
    ]
    assert check_orphan_pages(pages) == []


# ---------------------------------------------------------------------------
# audit_pages aggregator
# ---------------------------------------------------------------------------

def test_audit_pages_aggregates_per_page_and_cross_page():
    pages = [
        _page(url="https://x/a/", title="", meta_description="short"),
        _page(url="https://x/b/", title="dup", meta_description="ok ok ok ok ok ok ok ok ok ok ok ok ok"),
        _page(url="https://x/c/", title="dup", meta_description="ok ok ok ok ok ok ok ok ok ok ok ok ok"),
    ]
    issues = audit_pages(pages)
    types = {i["type"] for i in issues}
    assert "missing_title" in types
    assert "thin_meta_description" in types
    assert "duplicate_title" in types
