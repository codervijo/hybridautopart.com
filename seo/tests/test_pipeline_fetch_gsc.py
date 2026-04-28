from pipelines.fetch_gsc.main import (
    detect_csv_type,
    ingest_inbox,
    parse_indexing,
    parse_pages,
    parse_queries,
    read_csv,
)


# ---------------------------------------------------------------------------
# detect_csv_type
# ---------------------------------------------------------------------------

def test_detect_queries():
    assert detect_csv_type(["Query", "Clicks", "Impressions", "CTR", "Position"]) == "queries"


def test_detect_queries_top_queries_variant():
    assert detect_csv_type(["Top queries", "Clicks", "Impressions", "CTR", "Position"]) == "queries"


def test_detect_pages():
    assert detect_csv_type(["Page", "Clicks", "Impressions", "CTR", "Position"]) == "pages"


def test_detect_pages_top_pages_variant():
    assert detect_csv_type(["Top pages", "Clicks", "Impressions", "CTR", "Position"]) == "pages"


def test_detect_indexing_with_last_crawled():
    assert detect_csv_type(["URL", "Last crawled"]) == "indexing"


def test_detect_indexing_with_status():
    assert detect_csv_type(["URL", "Status"]) == "indexing"


def test_detect_unknown_falls_through():
    assert detect_csv_type(["Foo", "Bar"]) == "unknown"


# ---------------------------------------------------------------------------
# parse_queries
# ---------------------------------------------------------------------------

def test_parse_queries_normalizes_ctr_percent():
    headers = ["Query", "Clicks", "Impressions", "CTR", "Position"]
    rows = [["toyota prius", "100", "5,000", "2.0%", "12.5"]]
    out = parse_queries(headers, rows)
    assert out == [{"query": "toyota prius", "clicks": 100, "impressions": 5000, "ctr": 0.02, "position": 12.5}]


def test_parse_queries_handles_decimal_ctr():
    headers = ["Query", "Clicks", "Impressions", "CTR", "Position"]
    rows = [["psd simulator", "50", "1000", "0.05", "8.0"]]
    out = parse_queries(headers, rows)
    assert out[0]["ctr"] == 0.05


def test_parse_queries_skips_short_rows():
    headers = ["Query", "Clicks", "Impressions", "CTR", "Position"]
    rows = [[], ["x", "1"]]  # both incomplete in different ways
    out = parse_queries(headers, rows)
    # First row has no query column, skipped. Second has query but missing other cols → defaults to 0.
    assert len(out) == 1
    assert out[0]["query"] == "x"
    assert out[0]["clicks"] == 1
    assert out[0]["impressions"] == 0


# ---------------------------------------------------------------------------
# parse_pages
# ---------------------------------------------------------------------------

def test_parse_pages_with_top_pages_header():
    headers = ["Top pages", "Clicks", "Impressions", "CTR", "Position"]
    rows = [["https://hap.com/blog-en/x/", "10", "200", "5%", "9"]]
    out = parse_pages(headers, rows)
    assert out[0]["url"] == "https://hap.com/blog-en/x/"
    assert out[0]["ctr"] == 0.05


# ---------------------------------------------------------------------------
# parse_indexing
# ---------------------------------------------------------------------------

def test_parse_indexing_uses_status_column_when_present():
    headers = ["URL", "Status"]
    rows = [["https://hap.com/x/", "Crawled - currently not indexed"]]
    out = parse_indexing(headers, rows, "any.csv")
    assert out[0] == {"url": "https://hap.com/x/", "status": "Crawled - currently not indexed"}


def test_parse_indexing_falls_back_to_filename():
    # Many GSC indexing exports omit the status column — the filename is the status
    headers = ["URL", "Last crawled"]
    rows = [["https://hap.com/x/", "2026-04-20"]]
    out = parse_indexing(headers, rows, "Crawled_not_indexed.csv")
    assert out[0]["status"] == "crawled-not-indexed"


def test_parse_indexing_skips_empty_urls():
    headers = ["URL", "Last crawled"]
    rows = [["", "2026-04-20"], ["https://x/", "2026-04-21"]]
    out = parse_indexing(headers, rows, "any.csv")
    assert len(out) == 1


# ---------------------------------------------------------------------------
# ingest_inbox
# ---------------------------------------------------------------------------

def test_ingest_inbox_missing_dir(tmp_path):
    out = ingest_inbox(tmp_path / "does-not-exist")
    assert out["queries"] == []
    assert out["pages"] == []
    assert out["indexing"] == []


def test_ingest_inbox_empty_dir(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    out = ingest_inbox(inbox)
    assert out["files_seen"] == []


def test_ingest_inbox_routes_files_by_header(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "queries.csv").write_text(
        "Query,Clicks,Impressions,CTR,Position\nprius pwr mode,5,200,2.5%,15\n"
    )
    (inbox / "pages.csv").write_text(
        "Top pages,Clicks,Impressions,CTR,Position\nhttps://hap.com/blog-en/psd/,3,150,2%,10\n"
    )
    (inbox / "Crawled_not_indexed.csv").write_text(
        "URL,Last crawled\nhttps://hap.com/blog-en/orphan/,2026-04-20\n"
    )
    out = ingest_inbox(inbox)
    assert len(out["queries"]) == 1
    assert len(out["pages"]) == 1
    assert len(out["indexing"]) == 1
    assert out["indexing"][0]["status"] == "crawled-not-indexed"


def test_ingest_inbox_skips_unknown_headers(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "weird.csv").write_text("Foo,Bar\na,b\n")
    out = ingest_inbox(inbox)
    seen = {f["file"]: f["type"] for f in out["files_seen"]}
    assert seen["weird.csv"] == "unknown"


def test_ingest_inbox_extracts_zip_and_routes(tmp_path):
    """GSC exports always come zipped — auto-extract and walk recursively."""
    import zipfile
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    zip_path = inbox / "gsc-export.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("Queries.csv", "Query,Clicks,Impressions,CTR,Position\nprius,3,100,3%,9\n")
        z.writestr("Pages.csv", "Page,Clicks,Impressions,CTR,Position\nhttps://x/a/,2,50,4%,8\n")
    out = ingest_inbox(inbox)
    assert (inbox / "gsc-export").is_dir()  # extraction happened
    assert len(out["queries"]) == 1
    assert len(out["pages"]) == 1


def test_ingest_indexing_uses_metadata_status_when_present(tmp_path):
    """Coverage Drilldown exports include Metadata.csv with the real status name."""
    inbox = tmp_path / "inbox"
    sub = inbox / "Coverage-Drilldown"
    sub.mkdir(parents=True)
    (sub / "Table.csv").write_text(
        "URL,Last crawled\nhttps://x/a/,2026-04-20\nhttps://x/b/,2026-04-21\n"
    )
    (sub / "Metadata.csv").write_text(
        # Real GSC Coverage Drilldown exports use "Issue" as the property key
        "Property,Value\nSitemap,All known pages\nIssue,Crawled - currently not indexed\n"
    )
    out = ingest_inbox(inbox)
    assert len(out["indexing"]) == 2
    assert out["indexing"][0]["status"] == "Crawled - currently not indexed"


def test_ingest_inbox_zip_idempotent(tmp_path):
    """Re-running with the same zip already extracted shouldn't duplicate data."""
    import zipfile
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    zip_path = inbox / "gsc-export.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("Queries.csv", "Query,Clicks,Impressions,CTR,Position\nprius,3,100,3%,9\n")
    ingest_inbox(inbox)  # first run extracts
    out = ingest_inbox(inbox)  # second run sees extracted dir, skips re-extract
    # Still picks up the CSV via rglob — so query count is 1 from the extracted dir
    assert len(out["queries"]) == 1


# ---------------------------------------------------------------------------
# read_csv (BOM handling)
# ---------------------------------------------------------------------------

def test_read_csv_strips_bom(tmp_path):
    p = tmp_path / "with_bom.csv"
    # GSC exports often have a UTF-8 BOM
    p.write_bytes(b"\xef\xbb\xbfQuery,Clicks\nfoo,1\n")
    headers, rows = read_csv(p)
    assert headers == ["Query", "Clicks"]
    assert rows == [["foo", "1"]]
