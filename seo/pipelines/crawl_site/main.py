#!/usr/bin/env python3
"""crawl_site — fetch sitemap, polite per-URL crawl, write dated snapshot to data/crawls/."""

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.audit_state import write_dated
from lib.crawl import RateLimiter, RobotsChecker, fetch_page, fetch_sitemap, parse_page
from lib.env import load_env_file
from lib.io import append_jsonl, log, utc_now


def get_config() -> dict:
    load_env_file("../../seo.env", "crawl.env")
    return {
        "site_url":    os.environ.get("SITE_URL", "").rstrip("/"),
        "sitemap_url": os.environ.get("SITEMAP_URL", ""),
        "user_agent":  os.environ.get("USER_AGENT", "seo-audit-bot/0.1"),
        "delay_s":     int(os.environ.get("DELAY_MS", "500")) / 1000.0,
        "jitter_s":    int(os.environ.get("JITTER_MS", "200")) / 1000.0,
        "timeout":     int(os.environ.get("TIMEOUT", "30")),
        "data_root":   Path(os.environ.get("DATA_ROOT", "../../data")),
        "output_dir":  Path(os.environ.get("OUTPUT_DIR", "output")),
    }


def _load_existing(pages_jsonl: Path) -> tuple[set[str], list[dict]]:
    """Resume support: read previously-recorded pages from pages.jsonl."""
    done_urls: set[str] = set()
    existing: list[dict] = []
    if not pages_jsonl.exists():
        return done_urls, existing
    with open(pages_jsonl, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = rec.get("url")
            if url:
                done_urls.add(url)
                existing.append(rec)
    return done_urls, existing


def run() -> None:
    config = get_config()

    if not config["site_url"]:
        log("ERROR [CONFIG]: SITE_URL is not set in crawl.env")
        sys.exit(1)

    sitemap_url = config["sitemap_url"] or f"{config['site_url']}/sitemap_index.xml"
    site_host = urlparse(config["site_url"]).netloc

    output_dir: Path = config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    pages_jsonl = output_dir / "pages.jsonl"

    done_urls, existing = _load_existing(pages_jsonl)
    if done_urls:
        log(f"Resume: {len(done_urls)} pages already crawled (make clean-state to re-crawl)")

    log(f"Fetching sitemap: {sitemap_url}")
    urls = fetch_sitemap(sitemap_url, config["user_agent"], config["timeout"])
    log(f"Found {len(urls)} URL(s) in sitemap")

    robots = RobotsChecker(config["site_url"], config["user_agent"])
    rl = RateLimiter(delay_s=config["delay_s"], jitter_s=config["jitter_s"])

    new_pages: list[dict] = []
    skipped = blocked = failed = 0

    for i, url in enumerate(urls, start=1):
        if url in done_urls:
            skipped += 1
            continue
        if not robots.can_fetch(url):
            log(f"  [{i}/{len(urls)}] BLOCKED by robots: {url}")
            blocked += 1
            continue

        rl.wait()
        log(f"  [{i}/{len(urls)}] {url}")
        fetched = fetch_page(url, config["user_agent"], config["timeout"])
        parsed = parse_page(url, fetched["body"], site_host)

        record = {
            "url": url,
            "final_url": fetched["final_url"],
            "status": fetched["status"],
            "redirects": fetched["redirects"],
            "content_type": fetched["content_type"],
            "fetched_at": fetched["fetched_at"],
            **parsed,
        }
        if "error" in fetched:
            record["error"] = fetched["error"]
            failed += 1
        elif fetched["status"] >= 400 or fetched["status"] == 0:
            failed += 1

        append_jsonl(pages_jsonl, record)
        new_pages.append(record)

    payload = {
        "site": config["site_url"],
        "sitemap_url": sitemap_url,
        "crawled_at": utc_now(),
        "user_agent": config["user_agent"],
        "pages": existing + new_pages,
    }
    out_path = write_dated(config["data_root"], "crawls", payload)

    log(
        f"\nDone. urls={len(urls)} new={len(new_pages)} skipped={skipped} "
        f"blocked={blocked} failed={failed} → {out_path}"
    )


if __name__ == "__main__":
    run()
