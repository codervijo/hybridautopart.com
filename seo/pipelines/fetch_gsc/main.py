#!/usr/bin/env python3
"""fetch_gsc — normalize Google Search Console CSV exports into data/gsc/{date}.json.

V1: CSV-only ingest. The user drops GSC exports into data/gsc/inbox/, this
stage detects each file's type by header columns and merges into one JSON.

Supported CSV shapes (auto-detected by headers):
- Queries: "Top queries"/"Query", Clicks, Impressions, CTR, Position
- Pages:   "Top pages"/"Page", Clicks, Impressions, CTR, Position
- Coverage/indexing: "URL", "Last crawled" (or similar) — flagged-page exports

Idempotent: re-running on the same day overwrites that day's file only.
Empty inbox is normal — payload still written with empty arrays.
"""

import csv
import os
import sys
from pathlib import Path

_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.audit_state import write_dated
from lib.env import load_env_file
from lib.io import log, utc_now


def get_config() -> dict:
    load_env_file("../../seo.env", "gsc.env")
    return {
        "data_root": Path(os.environ.get("DATA_ROOT", "../../data")),
        "inbox":     Path(os.environ.get("GSC_INBOX", "../../data/gsc/inbox")),
        "site":      os.environ.get("SITE_URL", "").rstrip("/"),
    }


# ---------------------------------------------------------------------------
# CSV type detection + parsing
# ---------------------------------------------------------------------------

def _normalize_header(h: str) -> str:
    return h.strip().lower().replace(" ", "_")


def detect_csv_type(headers: list[str]) -> str:
    """Return 'queries', 'pages', 'indexing', or 'unknown'."""
    norm = {_normalize_header(h) for h in headers}
    has_metrics = "clicks" in norm and "impressions" in norm
    if has_metrics and ("query" in norm or "top_queries" in norm):
        return "queries"
    if has_metrics and ("page" in norm or "top_pages" in norm or "url" in norm):
        return "pages"
    if "url" in norm and any(k in norm for k in ("last_crawled", "discovery", "status", "first_detected")):
        return "indexing"
    return "unknown"


def _parse_ctr(value: str) -> float:
    """GSC exports CTR as '1.23%' or '0.0123'. Normalize to 0..1 fraction."""
    s = value.strip()
    if not s:
        return 0.0
    if s.endswith("%"):
        try:
            return float(s.rstrip("%")) / 100.0
        except ValueError:
            return 0.0
    try:
        v = float(s)
    except ValueError:
        return 0.0
    return v / 100.0 if v > 1.0 else v


def _parse_int(value: str) -> int:
    s = value.strip().replace(",", "")
    try:
        return int(s)
    except ValueError:
        return 0


def _parse_float(value: str) -> float:
    s = value.strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _column_index(headers: list[str], *candidates: str) -> int | None:
    norm = [_normalize_header(h) for h in headers]
    for c in candidates:
        if c in norm:
            return norm.index(c)
    return None


def parse_queries(headers: list[str], rows: list[list[str]]) -> list[dict]:
    iq = _column_index(headers, "query", "top_queries")
    ic = _column_index(headers, "clicks")
    ii = _column_index(headers, "impressions")
    ir = _column_index(headers, "ctr")
    ip = _column_index(headers, "position")
    out: list[dict] = []
    for row in rows:
        if iq is None or iq >= len(row):
            continue
        out.append({
            "query":       row[iq].strip(),
            "clicks":      _parse_int(row[ic]) if ic is not None and ic < len(row) else 0,
            "impressions": _parse_int(row[ii]) if ii is not None and ii < len(row) else 0,
            "ctr":         _parse_ctr(row[ir]) if ir is not None and ir < len(row) else 0.0,
            "position":    _parse_float(row[ip]) if ip is not None and ip < len(row) else 0.0,
        })
    return out


def parse_pages(headers: list[str], rows: list[list[str]]) -> list[dict]:
    iu = _column_index(headers, "page", "top_pages", "url")
    ic = _column_index(headers, "clicks")
    ii = _column_index(headers, "impressions")
    ir = _column_index(headers, "ctr")
    ip = _column_index(headers, "position")
    out: list[dict] = []
    for row in rows:
        if iu is None or iu >= len(row):
            continue
        out.append({
            "url":         row[iu].strip(),
            "clicks":      _parse_int(row[ic]) if ic is not None and ic < len(row) else 0,
            "impressions": _parse_int(row[ii]) if ii is not None and ii < len(row) else 0,
            "ctr":         _parse_ctr(row[ir]) if ir is not None and ir < len(row) else 0.0,
            "position":    _parse_float(row[ip]) if ip is not None and ip < len(row) else 0.0,
        })
    return out


def parse_indexing(headers: list[str], rows: list[list[str]], filename: str,
                   status_override: str | None = None) -> list[dict]:
    """Return list of {url, status}. Status derived from (in priority order):
    1. status_override (e.g. read from a sibling Metadata.csv)
    2. a Status/Reason column in the row
    3. the filename slug as a last-resort fallback
    """
    iu = _column_index(headers, "url")
    is_ = _column_index(headers, "status", "reason")
    fname_status = filename.lower().replace("_", "-").replace(".csv", "")
    out: list[dict] = []
    for row in rows:
        if iu is None or iu >= len(row):
            continue
        url = row[iu].strip()
        if not url:
            continue
        status = ""
        if is_ is not None and is_ < len(row):
            status = row[is_].strip()
        if not status:
            status = status_override or fname_status
        out.append({"url": url, "status": status})
    return out


def read_metadata_status(metadata_csv: Path) -> str | None:
    """Read a GSC Coverage Drilldown `Metadata.csv` (Property,Value rows) and return
    the Status/Reason value, or None if not present.
    """
    try:
        with open(metadata_csv, encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0].strip().lower() in ("issue", "status", "reason"):
                    return row[1].strip()
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Inbox walk
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    """Return (headers, rows)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return [], []
        rows = [r for r in reader if r]
    return headers, rows


def _extract_zips(inbox: Path) -> None:
    """Extract any *.zip in inbox into a subdir named after the zip stem.

    Idempotent: skips zips whose extraction subdir already exists.
    GSC exports always come zipped (Queries.csv, Pages.csv, Countries.csv, ...).
    """
    import zipfile
    for zip_path in sorted(inbox.glob("*.zip")):
        out_dir = inbox / zip_path.stem
        if out_dir.exists():
            log(f"  SKIP zip (already extracted): {zip_path.name}")
            continue
        out_dir.mkdir(parents=True)
        try:
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(out_dir)
        except zipfile.BadZipFile:
            log(f"  SKIP zip (corrupt): {zip_path.name}")
            out_dir.rmdir()
            continue
        log(f"  EXTRACTED: {zip_path.name} → {out_dir.name}/")


def ingest_inbox(inbox: Path) -> dict:
    """Walk inbox for *.csv (recursively), extract any zips first.

    Returns merged payload of queries/pages/indexing.
    """
    queries: list[dict] = []
    pages: list[dict] = []
    indexing: list[dict] = []
    files_seen: list[dict] = []

    if not inbox.exists():
        return {"queries": queries, "pages": pages, "indexing": indexing, "files_seen": files_seen}

    _extract_zips(inbox)

    for csv_path in sorted(inbox.rglob("*.csv")):
        headers, rows = read_csv(csv_path)
        if not headers:
            log(f"  SKIP (empty): {str(csv_path.relative_to(inbox))}")
            files_seen.append({"file": str(csv_path.relative_to(inbox)), "type": "empty", "rows": 0})
            continue
        kind = detect_csv_type(headers)
        if kind == "queries":
            new = parse_queries(headers, rows)
            queries.extend(new)
            count = len(new)
        elif kind == "pages":
            new = parse_pages(headers, rows)
            pages.extend(new)
            count = len(new)
        elif kind == "indexing":
            # Coverage Drilldown exports include a sibling Metadata.csv with the
            # actual status name; prefer that over the filename slug.
            metadata = csv_path.parent / "Metadata.csv"
            override = read_metadata_status(metadata) if metadata.exists() else None
            new = parse_indexing(headers, rows, csv_path.name, status_override=override)
            indexing.extend(new)
            count = len(new)
        else:
            log(f"  SKIP (unknown headers): {str(csv_path.relative_to(inbox))} — {headers[:5]}")
            files_seen.append({"file": str(csv_path.relative_to(inbox)), "type": "unknown", "rows": len(rows)})
            continue
        log(f"  OK [{kind}]: {str(csv_path.relative_to(inbox))} — {count} row(s)")
        files_seen.append({"file": str(csv_path.relative_to(inbox)), "type": kind, "rows": count})

    return {"queries": queries, "pages": pages, "indexing": indexing, "files_seen": files_seen}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run() -> None:
    config = get_config()
    inbox: Path = config["inbox"]

    log(f"Reading GSC CSVs from {inbox}")
    if not inbox.exists():
        log(f"  inbox does not exist; payload will be empty")

    parsed = ingest_inbox(inbox)
    summary = {
        "queries":  len(parsed["queries"]),
        "pages":    len(parsed["pages"]),
        "indexing": len(parsed["indexing"]),
        "files":    len(parsed["files_seen"]),
    }

    # GSC indexing exports often have a single status (filename-derived). Group:
    indexing_by_status: dict[str, list[str]] = {}
    for entry in parsed["indexing"]:
        indexing_by_status.setdefault(entry["status"], []).append(entry["url"])

    payload = {
        "fetched_at": utc_now(),
        "source": "csv",
        "site": config["site"],
        "summary": summary,
        "queries": parsed["queries"],
        "pages": parsed["pages"],
        "indexing": parsed["indexing"],
        "indexing_by_status": indexing_by_status,
        "files_seen": parsed["files_seen"],
    }

    out_path = write_dated(config["data_root"], "gsc", payload)
    log(f"Done. {summary} → {out_path}")


if __name__ == "__main__":
    run()
