#!/usr/bin/env python3
"""analyze_audit_results — turn raw audit data into prioritized human reports.

Reads from data/{crawls,audits/*,gsc,diffs}/latest.json (whatever exists today)
and writes data/reports/YYYY-MM-DD/{summary.md, todo.md, diff.md, details/*.md}.

Resilient: missing sibling-stage data is the normal case, not an error. Stub
sections are emitted with "_Stub:" prefix so future tools (e.g. compare_runs)
can grep for and skip them.
"""

import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

_SEO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SEO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEO_ROOT))

from lib.audit_state import read_latest, read_previous, today_str
from lib.env import load_env_file
from lib.io import atomic_write, log


# ---------------------------------------------------------------------------
# Impact / effort configuration
# ---------------------------------------------------------------------------

# Impact 5 = evidence-backed site-breaking (5xx, network errors, robots blocking,
#            sitemap missing, GSC-confirmed indexing failures).
# Impact 4 = confirmed signal-loss / content rejection (4xx, cross-lang canonical,
#            orphans, thin pages, dup clusters, title/H1 mismatch).
# Impact 3 = metadata/redirects/hygiene that hurts ranking but isn't broken.
# Impact 1-2 = cosmetic. 0 = uncategorized.
#
# `scaling`:
#   "per_unit"  — each occurrence is a separate fix; total effort = base × count
#   "fixed"     — one config/template fix solves all occurrences; effort doesn't scale
CHECK_META: dict[str, dict] = {
    # Critical (5) — evidence-backed broken
    "network_error": {"impact": 5, "effort": "30min", "scaling": "per_unit",
                      "title": "Network errors fetching pages",
                      "why": "Pages that won't fetch are unreachable to users and Google."},

    # High (4) — confirmed signal-loss
    "canonical_cross_language": {"impact": 4, "effort": "5min", "scaling": "fixed",
                                 "title": "Canonical points to different language path",
                                 "why": "English page canonicalising to a /fr/ URL tells Google to deprioritise the English version. Likely a Polylang misconfig — usually one settings change fixes all."},
    "thin_page": {"impact": 4, "effort": "2hr", "scaling": "per_unit",
                  "title": "Thin page (under threshold)",
                  "why": "Short content rates as low-value with Google; expand to compete in SERPs."},
    "duplicate_cluster": {"impact": 4, "effort": "half-day", "scaling": "fixed",
                          "title": "Near-duplicate content cluster",
                          "why": "Multiple pages on the same topic split ranking signal — consolidate or differentiate."},
    "orphan_page": {"impact": 4, "effort": "30min", "scaling": "per_unit",
                    "title": "Orphan page (no inbound internal links)",
                    "why": "Pages with no inbound link from other pages signal low importance to Google."},
    "title_h1_mismatch": {"impact": 4, "effort": "30min", "scaling": "per_unit",
                          "title": "Title and H1 don't match",
                          "why": "Divergent SERP title and on-page H1 tells users they landed on the wrong page."},
    "missing_title": {"impact": 4, "effort": "30min", "scaling": "per_unit",
                      "title": "Missing <title>",
                      "why": "Without a title, Google has nothing to display in SERPs."},

    # Medium (3) — metadata/redirects/hygiene
    "canonical_different_path": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                                 "title": "Canonical points to a different page (same language)",
                                 "why": "Could be intentional sub-page consolidation OR a misconfig. Needs human review."},
    "title_too_short": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                        "title": "Title under 30 chars",
                        "why": "Short titles miss keyword opportunities."},
    "title_too_long": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                       "title": "Title over 60 chars",
                       "why": "Truncated titles in SERPs hurt CTR."},
    "missing_meta_description": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                                 "title": "Missing meta description",
                                 "why": "Without a meta, Google writes its own snippet — usually a poor one."},
    "thin_meta_description": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                              "title": "Meta description under 50 chars",
                              "why": "Tiny metas leave SERP real estate empty and hurt CTR."},
    "meta_too_long": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                      "title": "Meta over 160 chars",
                      "why": "Truncated metas in SERPs lose the punchline."},
    "missing_canonical": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                          "title": "Missing canonical tag",
                          "why": "Without a canonical, Google may pick the wrong URL variant."},
    "missing_h1": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                   "title": "Missing H1",
                   "why": "Pages without an H1 lack the strongest on-page topic signal."},
    "multiple_h1": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                    "title": "Multiple H1s on one page",
                    "why": "More than one H1 dilutes the on-page topic signal."},
    "duplicate_title": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                        "title": "Duplicate <title> across pages",
                        "why": "Same title on multiple pages competes against itself in SERPs."},
    "duplicate_meta_description": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                                   "title": "Duplicate meta description",
                                   "why": "Identical metas split SERP real estate."},
    "redirect_chain": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                       "title": "Multi-hop redirect chains",
                       "why": "Each redirect loses link equity and slows page load."},
    "few_internal_links": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                           "title": "Page has fewer than 3 internal links",
                           "why": "Too few outgoing links isolates the page from the site's topic graph."},
    "many_outbound_links": {"impact": 3, "effort": "30min", "scaling": "per_unit",
                            "title": "Page has more than 20 outbound links",
                            "why": "Excessive outbound bleeds page authority."},
    "cross_language_link": {"impact": 3, "effort": "5min", "scaling": "fixed",
                            "title": "Internal links to wrong-language path",
                            "why": "Often one template change fixes hundreds of occurrences. SITE-SPECIFIC: /blog/ vs /blog-en/."},

    # Cosmetic — Impact 1
    "images_missing_alt": {"impact": 1, "effort": "30min", "scaling": "per_unit",
                           "title": "Images missing alt text",
                           "why": "Accessibility plus minor SEO signal."},
}


def _impact_for_http_status(check_type: str) -> dict:
    """http_4xx/5xx aren't fixed-key in CHECK_META; classify by code range."""
    if check_type.startswith("http_5"):
        return {"impact": 5, "effort": "30min", "scaling": "per_unit",
                "title": f"Server error ({check_type})",
                "why": "Server-side errors block users and Google from reaching the page."}
    if check_type.startswith("http_4"):
        return {"impact": 4, "effort": "30min", "scaling": "per_unit",
                "title": f"Broken page ({check_type})",
                "why": "4xx pages waste crawl budget and break user journeys."}
    return {"impact": 0, "effort": "30min", "scaling": "per_unit",
            "title": check_type,
            "why": "(uncategorized — tune CHECK_META in analyze_audit_results)"}


EFFORT_MINUTES = {
    "5min": 5,
    "30min": 30,
    "2hr": 120,
    "half-day": 240,
    "day+": 480,
    "multi-day": 1440,
}

# Re-bucket aggregate minutes back to a label (cap at multi-day).
_EFFORT_BUCKETS = [
    (5, "5min"),
    (30, "30min"),
    (120, "2hr"),
    (240, "half-day"),
    (480, "day+"),
]


def _bucket_minutes(minutes: int) -> str:
    for threshold, label in _EFFORT_BUCKETS:
        if minutes <= threshold:
            return label
    return "multi-day"


def aggregate_effort(base_effort: str, scaling: str, count: int) -> str:
    """Scale base effort by count for per-unit issues; fixed effort stays flat."""
    base = EFFORT_MINUTES.get(base_effort, 30)
    if scaling == "fixed" or count <= 1:
        total = base
    else:
        total = base * count
    return _bucket_minutes(total)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def get_config() -> dict:
    load_env_file("../../seo.env", "analyze.env")
    return {
        "data_root":   Path(os.environ.get("DATA_ROOT", "../../data")),
        "report_root": Path(os.environ.get("REPORT_ROOT", "../../data/reports")),
    }


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def collect_inputs(data_root: Path) -> dict:
    """Read every audit-stage's latest.json. Missing == None (normal case)."""
    return {
        "crawl":           read_latest(data_root, "crawls"),
        "audit_technical": read_latest(data_root, "audits/technical"),
        "audit_content":   read_latest(data_root, "audits/content"),
        "gsc":             read_latest(data_root, "gsc"),
        "diffs":           read_latest(data_root, "diffs"),
    }


# ---------------------------------------------------------------------------
# Item construction
# ---------------------------------------------------------------------------

def _slug(s: str) -> str:
    return s.replace("_", "-")


def _meta_for(check_type: str) -> dict:
    if check_type in CHECK_META:
        return CHECK_META[check_type]
    return _impact_for_http_status(check_type)


def build_items(inputs: dict) -> list[dict]:
    """Flatten audit findings into ranked todo items."""
    items: list[dict] = []

    at = inputs.get("audit_technical")
    if at:
        by_type: dict[str, list[str]] = defaultdict(list)
        for issue in at.get("issues", []):
            by_type[issue["type"]].append(issue["url"])
        for t, urls in by_type.items():
            urls = sorted(set(urls))
            meta = _meta_for(t)
            title = meta["title"]
            if len(urls) > 1:
                title = f"{title} ({len(urls)} pages)"
            items.append({
                "title": title,
                "why": meta["why"],
                "impact": meta["impact"],
                "effort": aggregate_effort(meta["effort"], meta.get("scaling", "per_unit"), len(urls)),
                "source": "audit_technical",
                "type_slug": _slug(t),
                "examples": urls,
            })

    ac = inputs.get("audit_content")
    if ac:
        thin = ac.get("thin_pages", [])
        if thin:
            meta = CHECK_META["thin_page"]
            urls = [p["url"] for p in thin]
            items.append({
                "title": f"{meta['title']} ({len(thin)} pages)",
                "why": meta["why"],
                "impact": meta["impact"],
                "effort": aggregate_effort(meta["effort"], meta.get("scaling", "per_unit"), len(thin)),
                "source": "audit_content",
                "type_slug": "thin-page",
                "examples": urls,
            })
        for i, cluster in enumerate(ac.get("duplicate_clusters", []), start=1):
            meta = CHECK_META["duplicate_cluster"]
            members = cluster["members"]
            items.append({
                "title": f"Duplicate cluster #{i} — {len(members)} pages, sim={cluster['max_similarity']}",
                "why": meta["why"],
                "impact": meta["impact"],
                "effort": aggregate_effort(meta["effort"], meta.get("scaling", "fixed"), 1),
                "source": "audit_content",
                "type_slug": f"duplicate-cluster-{i}",
                "examples": members,
            })

    items.sort(key=lambda x: (-x["impact"], EFFORT_MINUTES.get(x["effort"], 30)))
    _resolve_slug_collisions(items)
    return items


def _resolve_slug_collisions(items: list[dict]) -> None:
    """If the same type_slug appears at multiple impacts, append band suffix."""
    band_suffix = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "low", 0: "uncat"}
    impacts_per_slug: dict[str, set[int]] = defaultdict(set)
    for item in items:
        impacts_per_slug[item["type_slug"]].add(item["impact"])
    for item in items:
        if len(impacts_per_slug[item["type_slug"]]) > 1:
            item["type_slug"] = f"{item['type_slug']}-{band_suffix[item['impact']]}"


# ---------------------------------------------------------------------------
# Rendering — summary.md
# ---------------------------------------------------------------------------

def render_summary(inputs: dict, today: str) -> str:
    parts: list[str] = []
    parts.append(f"# SEO Audit Summary — {today}\n")
    parts.append("_Generated by analyze_audit_results from audit data in data/_\n")

    crawl = inputs["crawl"]
    if crawl is None:
        parts.append("## Crawl\n")
        parts.append("_Stub: crawl_site stage not yet producing data. This section will populate once data/crawls/{date}.json exists._\n")
    elif not crawl.get("pages"):
        parts.append("## Crawl\n")
        parts.append("_Empty: crawl_site ran but found no pages. Check sitemap URL._\n")
    else:
        pages = crawl["pages"]
        statuses = Counter(p["status"] for p in pages)
        parts.append("## Crawl\n")
        parts.append(f"- **Site:** {crawl.get('site', '?')}")
        parts.append(f"- **Pages crawled:** {len(pages)}")
        parts.append(f"- **HTTP statuses:** " + ", ".join(f"{c}×{n}" for c, n in sorted(statuses.items())))
        parts.append(f"- **Crawled at:** {crawl.get('crawled_at', '?')}\n")

    at = inputs["audit_technical"]
    if at is None:
        parts.append("## Technical audit\n")
        parts.append("_Stub: audit_technical stage not yet producing data. This section will populate once data/audits/technical/{date}.json exists._\n")
    elif at.get("summary", {}).get("issues_total", 0) == 0:
        parts.append("## Technical audit\n")
        parts.append("_Empty: audit_technical ran and found no issues._\n")
    else:
        s = at["summary"]
        parts.append("## Technical audit\n")
        parts.append(f"- **Total issues:** {s['issues_total']} across {s['total_pages']} pages")
        bt = sorted(s.get("by_type", {}).items(), key=lambda x: -x[1])
        if bt:
            parts.append("- **Top issue types:**")
            for t, c in bt[:5]:
                parts.append(f"  - `{t}`: {c}")
        parts.append("")

    ac = inputs["audit_content"]
    if ac is None:
        parts.append("## Content audit\n")
        parts.append("_Stub: audit_content stage not yet producing data. This section will populate once data/audits/content/{date}.json exists._\n")
    else:
        s = ac.get("summary", {})
        thresh = ac.get("thresholds", {})
        parts.append("## Content audit\n")
        parts.append(f"- **Thin pages** (< {thresh.get('thin_word_count', '?')} words): {s.get('thin_count', 0)}")
        parts.append(f"- **Duplicate clusters** (cosine ≥ {thresh.get('duplicate_cosine', '?')}): "
                     f"{s.get('duplicate_cluster_count', 0)} clusters, {s.get('duplicated_pages', 0)} pages")
        parts.append("")

    if inputs["gsc"] is None:
        parts.append("## GSC findings\n")
        parts.append("_Stub: fetch_gsc stage not yet producing data. This section will populate "
                     "once data/gsc/{date}.json exists._\n")
    else:
        # Schema not yet defined — fetch_gsc not built. When it ships, render real summary here.
        parts.append("## GSC findings\n")
        parts.append("_Empty: fetch_gsc stage produced data but renderer not yet wired up._\n")

    if inputs["diffs"] is None:
        parts.append("## Run-to-run regressions\n")
        parts.append("_Stub: compare_runs stage not yet producing data. This section will populate "
                     "once data/diffs/{date}.json exists._\n")
    else:
        parts.append("## Run-to-run regressions\n")
        parts.append("_Empty: compare_runs stage produced data but renderer not yet wired up._\n")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Rendering — todo.md
# ---------------------------------------------------------------------------

def _impact_band(impact: int) -> str:
    if impact == 5:
        return "Critical (impact 5)"
    if impact == 4:
        return "High (impact 4)"
    if impact == 3:
        return "Medium (impact 3)"
    if impact in (1, 2):
        return "Low (impact 1-2)"
    return "Uncategorized (impact 0)"


_BAND_ORDER = [
    "Critical (impact 5)",
    "High (impact 4)",
    "Medium (impact 3)",
    "Low (impact 1-2)",
    "Uncategorized (impact 0)",
]


def render_todo(items: list[dict], today: str, prev_run_date: str | None,
                net_new: int | None = None, net_resolved: int | None = None) -> str:
    lines: list[str] = []
    lines.append(f"# SEO Todo — {today}\n")
    lines.append("_Generated by analyze_audit_results from audit data in data/_\n")

    by_band: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_band[_impact_band(item["impact"])].append(item)

    for band in _BAND_ORDER:
        if not by_band.get(band):
            continue
        lines.append(f"## {band}")
        for item in by_band[band]:
            lines.append(f"- [ ] **{item['title']}** — {item['why']}")
            lines.append(f"  - Effort: {item['effort']} | Impact: {item['impact']} | Source: {item['source']}")
            ex = item["examples"]
            if not ex:
                continue
            shown = ex[:5]
            shown_str = ", ".join(shown)
            if len(ex) > 5:
                lines.append(f"  - Examples: {shown_str} (+{len(ex) - 5} more in details/{item['type_slug']}.md)")
            else:
                lines.append(f"  - Examples: {shown_str}")
        lines.append("")

    lines.append("## Notes")
    lines.append(f"- Total items: {len(items)}")
    lines.append(f"- Previous run: {prev_run_date or 'none'}")
    if net_new is not None and net_resolved is not None:
        lines.append(f"- Net change: +{net_new} new, -{net_resolved} resolved")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Rendering — diff.md
# ---------------------------------------------------------------------------

def render_diff(inputs: dict, data_root: Path, today: str) -> tuple[str, dict]:
    """Return (diff_md, stats). stats has net_new/net_resolved for todo's notes."""
    parts: list[str] = []
    parts.append(f"# Diff — {today}\n")
    parts.append("_Generated by analyze_audit_results._\n")

    found_any = False
    stats = {"net_new": 0, "net_resolved": 0, "prev_run_date": None}

    at_today = inputs["audit_technical"]
    at_prev = read_previous(data_root, "audits/technical", before=today)
    if at_today and at_prev:
        found_any = True
        prev_date = (at_prev.get("audited_at") or "")[:10] or "?"
        stats["prev_run_date"] = prev_date
        today_keys = {(i["url"], i["type"]) for i in at_today.get("issues", [])}
        prev_keys = {(i["url"], i["type"]) for i in at_prev.get("issues", [])}
        new = today_keys - prev_keys
        resolved = prev_keys - today_keys
        stats["net_new"] += len(new)
        stats["net_resolved"] += len(resolved)
        parts.append(f"## Technical audit (vs {prev_date})\n")
        parts.append(f"- New issues: {len(new)}")
        parts.append(f"- Resolved issues: {len(resolved)}\n")
        if new:
            parts.append("### New today (top 10)")
            for url, t in sorted(new)[:10]:
                parts.append(f"- `{t}` on {url}")
            parts.append("")
        if resolved:
            parts.append("### Resolved today (top 10)")
            for url, t in sorted(resolved)[:10]:
                parts.append(f"- `{t}` on {url}")
            parts.append("")

    ac_today = inputs["audit_content"]
    ac_prev = read_previous(data_root, "audits/content", before=today)
    if ac_today and ac_prev:
        found_any = True
        prev_date = (ac_prev.get("audited_at") or "")[:10] or "?"
        stats["prev_run_date"] = stats["prev_run_date"] or prev_date
        today_thin = {p["url"] for p in ac_today.get("thin_pages", [])}
        prev_thin = {p["url"] for p in ac_prev.get("thin_pages", [])}
        new_thin = today_thin - prev_thin
        resolved_thin = prev_thin - today_thin
        stats["net_new"] += len(new_thin)
        stats["net_resolved"] += len(resolved_thin)
        parts.append(f"## Content audit (vs {prev_date})\n")
        parts.append(f"- New thin pages: {len(new_thin)}")
        parts.append(f"- Resolved thin pages: {len(resolved_thin)}")
        # Cluster identity isn't stable across runs — defer until compare_runs lands.
        parts.append("- Cluster diff: skipped in v1 (cluster identity not stable across runs)\n")

    if not found_any:
        parts.append("_Stub: no previous run found in data/. This file will populate once a second day's audit exists._\n")

    return "\n".join(parts), stats


# ---------------------------------------------------------------------------
# Rendering — details/<slug>.md
# ---------------------------------------------------------------------------

def render_details(items: list[dict], report_dir: Path) -> list[Path]:
    """Write a per-item details file for any item with > 5 examples. Return paths written."""
    written: list[Path] = []
    for item in items:
        if len(item["examples"]) <= 5:
            continue
        details_dir = report_dir / "details"
        details_dir.mkdir(parents=True, exist_ok=True)
        path = details_dir / f"{item['type_slug']}.md"
        body = [f"# {item['title']}\n"]
        body.append(f"_All {len(item['examples'])} occurrences. Generated by analyze_audit_results._\n")
        body.append(f"- Impact: {item['impact']}")
        body.append(f"- Effort: {item['effort']}")
        body.append(f"- Source: {item['source']}")
        body.append(f"- Why: {item['why']}\n")
        body.append("## URLs\n")
        for u in item["examples"]:
            body.append(f"- {u}")
        atomic_write(path, "\n".join(body) + "\n")
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run() -> None:
    config = get_config()
    today = today_str()
    data_root: Path = config["data_root"]
    report_dir: Path = config["report_root"] / today
    report_dir.mkdir(parents=True, exist_ok=True)

    inputs = collect_inputs(data_root)
    log("Inputs: " + ", ".join(f"{k}={'ok' if v is not None else 'missing'}" for k, v in inputs.items()))

    items = build_items(inputs)
    diff_md, diff_stats = render_diff(inputs, data_root, today)
    summary_md = render_summary(inputs, today)
    todo_md = render_todo(
        items,
        today,
        prev_run_date=diff_stats["prev_run_date"],
        net_new=diff_stats["net_new"] if diff_stats["prev_run_date"] else None,
        net_resolved=diff_stats["net_resolved"] if diff_stats["prev_run_date"] else None,
    )

    atomic_write(report_dir / "summary.md", summary_md)
    atomic_write(report_dir / "todo.md", todo_md)
    atomic_write(report_dir / "diff.md", diff_md)
    details_paths = render_details(items, report_dir)

    log(f"Done. items={len(items)} details_files={len(details_paths)} → {report_dir}")


if __name__ == "__main__":
    run()
