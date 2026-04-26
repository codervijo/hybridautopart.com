from pipelines.audit_content.main import (
    dedupe_by_url,
    find_duplicate_clusters,
    find_thin_pages,
)


def _page(**overrides) -> dict:
    base = {
        "url": "https://hybridautopart.com/blog-en/x/",
        "status": 200,
        "word_count": 1500,
        "text": "Toyota Prius hybrid battery system explanation page content here.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# dedupe_by_url
# ---------------------------------------------------------------------------

def test_dedupe_first_wins():
    pages = [
        _page(url="https://x/a/", word_count=100),
        _page(url="https://x/a/", word_count=999),
    ]
    out = dedupe_by_url(pages)
    assert len(out) == 1
    assert out[0]["word_count"] == 100


# ---------------------------------------------------------------------------
# find_thin_pages
# ---------------------------------------------------------------------------

def test_thin_pages_flagged_below_threshold():
    pages = [
        _page(url="https://x/a/", word_count=500),
        _page(url="https://x/b/", word_count=1200),
        _page(url="https://x/c/", word_count=799),
    ]
    out = find_thin_pages(pages, threshold=800)
    urls = [p["url"] for p in out]
    assert urls == ["https://x/a/", "https://x/c/"]  # sorted by word_count asc


def test_thin_pages_skips_non_200():
    pages = [
        _page(url="https://x/a/", word_count=100, status=404),
        _page(url="https://x/b/", word_count=200, status=200),
    ]
    out = find_thin_pages(pages, threshold=800)
    assert [p["url"] for p in out] == ["https://x/b/"]


def test_thin_pages_threshold_inclusive_at_zero():
    pages = [_page(word_count=0)]
    assert len(find_thin_pages(pages, threshold=800)) == 1


# ---------------------------------------------------------------------------
# find_duplicate_clusters
# ---------------------------------------------------------------------------

def test_clusters_flag_near_duplicates():
    # Two pages with very similar content should cluster
    same_text = ("Toyota Prius hybrid battery degradation symptoms "
                 "include reduced fuel economy and longer engine runtime. "
                 "Battery replacement options include OEM and refurbished units. ") * 5
    pages = [
        _page(url="https://x/a/", text=same_text),
        _page(url="https://x/b/", text=same_text),
        _page(url="https://x/c/",
              text="Bicycle wheel frame chain pedal handlebar saddle gear "
                   "components for road riding completely different topic. " * 5),
    ]
    out = find_duplicate_clusters(pages, threshold=0.5)
    assert len(out) == 1
    assert set(out[0]["members"]) == {"https://x/a/", "https://x/b/"}
    assert out[0]["max_similarity"] >= 0.5


def test_clusters_skip_empty_text():
    pages = [
        _page(url="https://x/a/", text=""),
        _page(url="https://x/b/", text=""),
    ]
    assert find_duplicate_clusters(pages, threshold=0.5) == []


def test_clusters_skip_non_200():
    same = "shared shared shared shared content " * 10
    pages = [
        _page(url="https://x/a/", text=same, status=404),
        _page(url="https://x/b/", text=same, status=200),
    ]
    # Only one page is eligible → no cluster
    assert find_duplicate_clusters(pages, threshold=0.5) == []


def test_clusters_returns_urls_not_indices():
    same = "shared shared shared shared content here " * 10
    pages = [
        _page(url="https://x/a/", text=same),
        _page(url="https://x/b/", text=same),
        # Third doc keeps IDF > 0 for the shared vocab so the dup pair has signal
        _page(url="https://x/c/", text="completely different unrelated topic words " * 10),
    ]
    out = find_duplicate_clusters(pages, threshold=0.5)
    assert all(isinstance(m, str) and m.startswith("https://") for m in out[0]["members"])
