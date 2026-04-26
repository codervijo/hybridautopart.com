#!/usr/bin/env python3
"""audit_technical — pure transform: latest crawl → flagged technical issues."""

import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.audit_state import read_latest, write_dated
from lib.env import load_env_file
from lib.io import log, utc_now


def get_config() -> dict:
    load_env_file("../../seo.env", "audit.env")
    return {
        "data_root": Path(os.environ.get("DATA_ROOT", "../../data")),
    }


# ---------------------------------------------------------------------------
# Per-page checks
# ---------------------------------------------------------------------------

def check_status(page: dict) -> list[dict]:
    s = page["status"]
    if s == 0:
        return [{"url": page["url"], "type": "network_error", "detail": page.get("error", "")}]
    if s >= 400:
        return [{"url": page["url"], "type": f"http_{s}", "detail": ""}]
    return []


def check_redirect_chain(page: dict) -> list[dict]:
    chain = page.get("redirects", [])
    if len(chain) > 1:
        path = " -> ".join(r["from"] for r in chain) + f" -> {chain[-1]['to']}"
        return [{"url": page["url"], "type": "redirect_chain", "detail": f"{len(chain)} hops: {path}"}]
    return []


def check_missing_title(page: dict) -> list[dict]:
    if page["status"] != 200:
        return []
    if not page.get("title", "").strip():
        return [{"url": page["url"], "type": "missing_title", "detail": ""}]
    return []


def check_title_length(page: dict) -> list[dict]:
    """Flag titles outside the 30–60 char range Google displays cleanly."""
    if page["status"] != 200:
        return []
    title = page.get("title", "").strip()
    if not title:
        return []
    n = len(title)
    if n < 30:
        return [{"url": page["url"], "type": "title_too_short", "detail": f"{n} chars: {title!r}"}]
    if n > 60:
        return [{"url": page["url"], "type": "title_too_long", "detail": f"{n} chars: {title!r}"}]
    return []


def check_missing_meta(page: dict) -> list[dict]:
    if page["status"] != 200:
        return []
    if not page.get("meta_description", "").strip():
        return [{"url": page["url"], "type": "missing_meta_description", "detail": ""}]
    return []


def check_thin_meta(page: dict) -> list[dict]:
    """Meta < 50 chars is too thin to compete in SERPs."""
    if page["status"] != 200:
        return []
    meta = page.get("meta_description", "").strip()
    if 0 < len(meta) < 50:
        return [{"url": page["url"], "type": "thin_meta_description",
                 "detail": f"{len(meta)} chars: {meta!r}"}]
    return []


def check_meta_too_long(page: dict) -> list[dict]:
    """Meta > 160 chars gets truncated by Google."""
    if page["status"] != 200:
        return []
    meta = page.get("meta_description", "").strip()
    if len(meta) > 160:
        return [{"url": page["url"], "type": "meta_too_long",
                 "detail": f"{len(meta)} chars"}]
    return []


def check_h1_count(page: dict) -> list[dict]:
    """Exactly one H1 expected. 0 or >1 are both red flags."""
    if page["status"] != 200:
        return []
    h1s = page.get("h1") or []
    if len(h1s) == 0:
        return [{"url": page["url"], "type": "missing_h1", "detail": ""}]
    if len(h1s) > 1:
        return [{"url": page["url"], "type": "multiple_h1",
                 "detail": f"{len(h1s)} H1s: {h1s}"}]
    return []


def _word_set(s: str) -> set[str]:
    """Lowercase tokens >2 chars. Crude but fine for fuzzy title/H1 matching."""
    return {w.lower().strip(".,:;!?\"'()[]") for w in s.split() if len(w) > 2}


def check_title_h1_mismatch(page: dict) -> list[dict]:
    """Flag pages where title and first H1 don't share at least half their words."""
    if page["status"] != 200:
        return []
    title = page.get("title", "").strip()
    h1s = page.get("h1") or []
    if not title or not h1s:
        return []
    t = _word_set(title)
    h = _word_set(h1s[0])
    if not t or not h:
        return []
    overlap = len(t & h) / len(t | h)
    # 0.6 catches the audit's HSD page case (overlap == 0.5) without firing on
    # close matches like "Foo Bar" vs "Foo Bar Baz" (overlap ~0.67).
    if overlap < 0.6:
        return [{"url": page["url"], "type": "title_h1_mismatch",
                 "detail": f"overlap={overlap:.2f} title={title!r} h1={h1s[0]!r}"}]
    return []


def check_internal_link_count(page: dict) -> list[dict]:
    """Fewer than 3 internal links suggests a near-orphan page."""
    if page["status"] != 200:
        return []
    n = len(page.get("internal_links", []))
    if n < 3:
        return [{"url": page["url"], "type": "few_internal_links", "detail": f"{n} link(s)"}]
    return []


def check_outbound_link_count(page: dict) -> list[dict]:
    """More than 20 outbound links bleeds page authority."""
    if page["status"] != 200:
        return []
    n = len(page.get("outbound_links", []))
    if n > 20:
        return [{"url": page["url"], "type": "many_outbound_links", "detail": f"{n} link(s)"}]
    return []


def check_images_missing_alt(page: dict) -> list[dict]:
    if page["status"] != 200:
        return []
    n = page.get("images_without_alt", 0)
    if n > 0:
        return [{"url": page["url"], "type": "images_missing_alt", "detail": f"{n} image(s)"}]
    return []


def check_missing_canonical(page: dict) -> list[dict]:
    if page["status"] != 200:
        return []
    if not page.get("canonical", "").strip():
        return [{"url": page["url"], "type": "missing_canonical", "detail": ""}]
    return []


def check_canonical_mismatch(page: dict) -> list[dict]:
    if page["status"] != 200:
        return []
    canonical = page.get("canonical", "").strip()
    if not canonical:
        return []
    final = page.get("final_url", page["url"])
    if canonical.rstrip("/") != final.rstrip("/"):
        return [{"url": page["url"], "type": "canonical_mismatch",
                 "detail": f"canonical={canonical} final_url={final}"}]
    return []


def check_cross_language_link(page: dict) -> list[dict]:
    """SITE-SPECIFIC: flag internal links to /blog/ (French path) — should be /blog-en/."""
    issues = []
    for link in page.get("internal_links", []):
        path = urlparse(link).path
        if path.startswith("/blog/") and not path.startswith("/blog-en/"):
            issues.append({"url": page["url"], "type": "cross_language_link",
                           "detail": f"link to French path: {link}"})
    return issues


# ---------------------------------------------------------------------------
# Cross-page checks
# ---------------------------------------------------------------------------

def check_duplicates(pages: list[dict], field: str, issue_type: str) -> list[dict]:
    """Flag pages sharing the same `field` value."""
    by_value: dict[str, list[str]] = defaultdict(list)
    for p in pages:
        if p["status"] != 200:
            continue
        v = (p.get(field) or "").strip()
        if v:
            by_value[v].append(p["url"])
    issues = []
    for v, urls in by_value.items():
        if len(urls) > 1:
            for u in urls:
                others = [x for x in urls if x != u]
                issues.append({"url": u, "type": issue_type,
                               "detail": f"{field}={v!r} shared with {len(others)} other(s)"})
    return issues


def _normalize_url(url: str) -> str:
    """Strip query/fragment for orphan detection. Keeps trailing slash as-is."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def check_orphan_pages(pages: list[dict]) -> list[dict]:
    """Pages with no inbound internal link from any other crawled page (self-links excluded)."""
    inbound: set[str] = set()
    for p in pages:
        src = _normalize_url(p["url"])
        for link in p.get("internal_links", []):
            dst = _normalize_url(link)
            if dst != src:
                inbound.add(dst)
    issues = []
    for p in pages:
        if p["status"] != 200:
            continue
        if _normalize_url(p["url"]) not in inbound:
            issues.append({"url": p["url"], "type": "orphan_page", "detail": ""})
    return issues


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def dedupe_by_url(pages: list[dict]) -> list[dict]:
    """First-wins dedup. pages.jsonl may have dupes (e.g., Yoast emits / in multiple sitemaps)."""
    seen: set[str] = set()
    out: list[dict] = []
    for p in pages:
        u = p.get("url", "")
        if u in seen:
            continue
        seen.add(u)
        out.append(p)
    return out


def audit_pages(pages: list[dict]) -> list[dict]:
    pages = dedupe_by_url(pages)
    issues: list[dict] = []
    for p in pages:
        issues.extend(check_status(p))
        issues.extend(check_redirect_chain(p))
        issues.extend(check_missing_title(p))
        issues.extend(check_title_length(p))
        issues.extend(check_missing_meta(p))
        issues.extend(check_thin_meta(p))
        issues.extend(check_meta_too_long(p))
        issues.extend(check_missing_canonical(p))
        issues.extend(check_canonical_mismatch(p))
        issues.extend(check_h1_count(p))
        issues.extend(check_title_h1_mismatch(p))
        issues.extend(check_internal_link_count(p))
        issues.extend(check_outbound_link_count(p))
        issues.extend(check_images_missing_alt(p))
        issues.extend(check_cross_language_link(p))
    issues.extend(check_duplicates(pages, "title", "duplicate_title"))
    issues.extend(check_duplicates(pages, "meta_description", "duplicate_meta_description"))
    issues.extend(check_orphan_pages(pages))
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run() -> None:
    config = get_config()
    data_root: Path = config["data_root"]

    crawl = read_latest(data_root, "crawls")
    if crawl is None:
        log("ERROR [NO_CRAWL]: data/crawls/latest.json not found — run crawl_site first")
        sys.exit(1)

    pages = crawl.get("pages", [])
    log(f"Auditing {len(pages)} page(s) from crawl at {crawl.get('crawled_at')}")

    issues = audit_pages(pages)

    payload = {
        "audited_at": utc_now(),
        "site": crawl.get("site"),
        "source_crawl_at": crawl.get("crawled_at"),
        "summary": {
            "total_pages": len(pages),
            "issues_total": len(issues),
            "by_type": dict(Counter(i["type"] for i in issues)),
        },
        "issues": issues,
    }

    out_path = write_dated(data_root, "audits/technical", payload)
    log(f"Done. issues={len(issues)} → {out_path}")
    for issue_type, count in sorted(payload["summary"]["by_type"].items(), key=lambda x: -x[1]):
        log(f"  {issue_type}: {count}")


if __name__ == "__main__":
    run()
