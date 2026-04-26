#!/usr/bin/env python3
"""audit_content — pure transform: latest crawl → thin pages + near-duplicate clusters."""

import os
import sys
from pathlib import Path

_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.audit_state import read_latest, write_dated
from lib.env import load_env_file
from lib.io import log, utc_now
from lib.similarity import cluster_by_threshold, tfidf_vectors, tokenize


def get_config() -> dict:
    load_env_file("../../seo.env", "audit.env")
    return {
        "data_root":     Path(os.environ.get("DATA_ROOT", "../../data")),
        "thin_words":    int(os.environ.get("THIN_WORDS", "800")),
        "dup_threshold": float(os.environ.get("DUP_THRESHOLD", "0.75")),
    }


def dedupe_by_url(pages: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for p in pages:
        u = p.get("url", "")
        if u in seen:
            continue
        seen.add(u)
        out.append(p)
    return out


def find_thin_pages(pages: list[dict], threshold: int) -> list[dict]:
    """Pages with word_count below threshold (status==200 only)."""
    thin = []
    for p in pages:
        if p.get("status") != 200:
            continue
        wc = p.get("word_count", 0)
        if wc < threshold:
            thin.append({"url": p["url"], "word_count": wc})
    return sorted(thin, key=lambda x: x["word_count"])


def find_duplicate_clusters(pages: list[dict], threshold: float) -> list[dict]:
    """Cluster pages whose TF-IDF cosine similarity >= threshold.

    Skips pages with empty text — those are either non-200 or failed parses.
    """
    eligible = [p for p in pages if p.get("status") == 200 and p.get("text", "")]
    if len(eligible) < 2:
        return []

    docs = [tokenize(p["text"]) for p in eligible]
    vecs = tfidf_vectors(docs)
    raw = cluster_by_threshold(vecs, threshold)

    return [
        {
            "members": [eligible[i]["url"] for i in c["members"]],
            "max_similarity": round(c["max_similarity"], 3),
        }
        for c in raw
    ]


def run() -> None:
    config = get_config()
    data_root: Path = config["data_root"]

    crawl = read_latest(data_root, "crawls")
    if crawl is None:
        log("ERROR [NO_CRAWL]: data/crawls/latest.json not found — run crawl_site first")
        sys.exit(1)

    pages = dedupe_by_url(crawl.get("pages", []))
    log(f"Auditing {len(pages)} page(s) from crawl at {crawl.get('crawled_at')}")

    has_text = sum(1 for p in pages if p.get("text"))
    if has_text == 0:
        log("ERROR [NO_TEXT]: crawl records have no `text` field — re-crawl needed "
            "(make clean-state && make run in crawl_site)")
        sys.exit(2)
    if has_text < len(pages):
        log(f"WARNING: only {has_text}/{len(pages)} pages have text — "
            "duplicate detection will skip the rest")

    thin = find_thin_pages(pages, config["thin_words"])
    clusters = find_duplicate_clusters(pages, config["dup_threshold"])

    payload = {
        "audited_at": utc_now(),
        "site": crawl.get("site"),
        "source_crawl_at": crawl.get("crawled_at"),
        "thresholds": {
            "thin_word_count": config["thin_words"],
            "duplicate_cosine": config["dup_threshold"],
        },
        "summary": {
            "total_pages": len(pages),
            "thin_count": len(thin),
            "duplicate_cluster_count": len(clusters),
            "duplicated_pages": sum(len(c["members"]) for c in clusters),
        },
        "thin_pages": thin,
        "duplicate_clusters": clusters,
    }

    out_path = write_dated(data_root, "audits/content", payload)
    log(f"Done. thin={len(thin)} dup_clusters={len(clusters)} → {out_path}")
    if thin:
        log(f"  Thinnest: {thin[0]['url']} ({thin[0]['word_count']} words)")
    if clusters:
        top = clusters[0]
        log(f"  Strongest cluster (sim={top['max_similarity']}): {len(top['members'])} pages")


if __name__ == "__main__":
    run()
