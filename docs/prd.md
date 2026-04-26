# PRD — hybridautopart.com Content Machine

---

## V1 — Content Machine for hybridautopart.com
**Status:** Live — real SEO traffic, <1k visits/month

| Phase | Feature | Type | Status |
|-------|---------|------|--------|
| P1 | Dual-provider API support (Claude + OpenAI) | Pipeline | [ ] |
| P1 | Emergency SEO fixes (sidebar, keyword spam, factual errors) | Content | [ ] |
| P1 | Title + meta description blitz (8 pages) | Content | [ ] |
| P1 | Schema + category structure (breadcrumbs, FAQ, Article) | Content | [ ] |
| P1 | Content expansion — top 3 pages | Content | [ ] |
| P1 | Amazon Associates setup + affiliate links | Revenue | [ ] |
| P1 | Content velocity — 12 new posts | Content | [ ] |
| P1 | PSD Simulator React plugin launch | Tool | [ ] |
| P2 | Toyota hybrid model expansion — 5 clusters | Content | [ ] |
| P2 | Interactive tools — Savings Calculator, Battery Estimator, Model Comparison | Tool | [ ] |
| P2 | SEO checker pipeline — per-post audit on publish (title, meta, schema, links, word count) | Pipeline | [ ] |
| P2 | Technical SEO checker — site-wide crawl: broken links, canonical, Core Web Vitals, sitemap | Pipeline | [ ] |
| P2 | On-page quality gate — block publish if post fails minimum SEO score | Pipeline | [ ] |
| P2 | Provider comparison — run write_articles with Claude and OpenAI on same topics, diff output quality | Research | [ ] |
| P2 | Cross-linking pipeline — auto-generate internal link suggestions for every page and post | Pipeline | [ ] |
| P2 | crawl_site stage — sitemap-driven polite crawler, dated per-URL snapshots in `data/crawls/` | Pipeline | [ ] |
| P2 | audit_content stage — thin-page detector + near-duplicate clustering (TF-IDF cosine, stdlib) | Pipeline | [ ] |
| P2 | fetch_gsc stage (CSV) — normalize Search Console exports into `data/gsc/` (incl. Crawled-not-indexed) | Pipeline | [ ] |
| P2 | compare_runs stage — diff today's audit vs previous, flag regressions (deindex, CTR drop, new thin) | Pipeline | [ ] |
| P2 | triage stage — synthesize crawl + audits + GSC into prioritized improve/consolidate/create/fix lists | Pipeline | [ ] |
| P2 | generate_article_ideas reads triage — seed new topics from GSC-impressions-without-page gaps | Pipeline | [ ] |
| P2 | revise_articles reads content audit — depth/dedupe directives injected for flagged thin/duplicate posts | Pipeline | [ ] |
| P2 | Mediavine application + email newsletter | Revenue | [ ] |
| P3 | Backlink strategy — HARO, outreach, guest posts | Growth | [ ] |
| P3 | Content scale — 144 posts + used car + DIY guides | Content | [ ] |
| P3 | YouTube companion channel | Channel | [ ] |
| P3 | Revenue at 100K — ads + affiliate + sponsored + newsletter | Revenue | [ ] |

---

## Phase 1 — Foundation & Recovery
Target: 833 → 3,000 visits/month

### Pipeline: dual-provider API support
- [ ] Add `call_llm(system, user, config)` to `lib/http.py` — auto-detects provider from `API_URL`
- [ ] Anthropic path: `x-api-key` header, `anthropic-version`, `{"system": ..., "messages": [...]}` request shape, `result["content"][0]["text"]` extraction
- [ ] OpenAI path: `Authorization: Bearer` header, `{"messages": [system, user]}` request shape, `result["choices"][0]["message"]["content"]` extraction
- [ ] All pipeline `generate_ai()` functions delegate to `call_llm` — no per-pipeline provider logic
- [ ] Switch provider by changing `API_URL` + `MODEL` + `API_KEY` in `seo.env` only
- [ ] Tests: mock both response shapes, assert correct extraction per provider

### Emergency fixes
- [ ] Remove Lamill Web Systems attribution from About Us sidebar
- [ ] Delete "Covers:" keyword spam from prius-pwr-mode
- [ ] Remove Subaru Crosstrek from Toyota PSD vehicle list (factual error)
- [ ] Fix broken `/blog/` → `/blog-en/` redirect in `.htaccess`
- [ ] Update footer © year to dynamic
- [ ] Fix H1/title mismatch on toyota-hybrid-synergy-drive-problems page

### Title & meta blitz
- [ ] Rewrite SEO titles + H1s for all 8 top pages
- [ ] Paste all 25 prepared meta descriptions into Yoast

### Schema & structure
- [ ] Enable Yoast breadcrumbs + Article schema
- [ ] Create 5 topic categories; reassign all 46 posts
- [ ] Add FAQ schema JSON-LD to top 8 posts

### Content expansion
- [ ] Expand prius-pwr-mode to 2,800 words (ECO/PWR table, Gen 5 section)
- [ ] Expand toyota-prius-power-split-device to 3,500 words (Willis equation, 6 operating modes)
- [ ] Expand prius-0-60 with complete model-year table 2001–2024

### Content velocity
- [ ] Set up Amazon Associates affiliate account
- [ ] Add affiliate links to top 5 existing posts
- [ ] Launch 12 new posts (3/week) — see topic queue in `seo/topics.json`

### PSD Simulator launch
- [ ] Complete React plugin build and deploy to WordPress
- [ ] Write dedicated "PSD Simulator" post
- [ ] Execute launch outreach (r/prius, r/Toyota, LinkedIn, PriusChat)

---

## Phase 2 — Content Machine
Target: 3,000 → 10,000 visits/month

### Toyota hybrid model expansion
- [ ] RAV4 Hybrid: 12-post cluster
- [ ] Camry Hybrid + battery deep-dive cluster
- [ ] Corolla Hybrid + featured snippet targeting
- [ ] Highlander Hybrid + family comparison content
- [ ] Prius Prime + EV/PHEV content

### Interactive tools
- [ ] Hybrid vs Gas Savings Calculator (React plugin)
- [ ] Hybrid Battery Health Estimator (React plugin)
- [ ] Toyota Hybrid Model Comparison Tool (React plugin)

### Cross-linking pipeline
- [ ] Crawl all published posts and pages; build a keyword → URL index
- [ ] For each post, identify 5–10 outbound link opportunities to other site content based on semantic overlap
- [ ] Output: `output/cross-links.md` — per-post table of suggested anchor text + target URL + insertion point (nearest heading)
- [ ] Optional: WP REST API mode — insert links directly into post body as HTML in WordPress drafts

### Provider comparison — Claude vs OpenAI
- [ ] Run `write_articles` on the same 5 topics twice — once with `claude-sonnet-4-6`, once with `gpt-4.1-mini`
- [ ] Score both outputs with `review_articles` pipeline (HCU, structure, engagement scores)
- [ ] Manual review: engineering depth, factual accuracy, word quality
- [ ] Decision output: preferred provider per use-case (long-form vs short, commercial vs informational)
- [ ] Set winning provider as default in `seo.env`; keep loser available as override

### SEO checker pipelines
- [ ] **Per-post SEO checker** — runs automatically after `revise_articles`; scores each post against: title length (50–60 chars), meta description present (145–160 chars), primary keyword in first 100 words, at least 3 internal links, FAQ schema present, word count ≥ target; outputs `seo-score.json` per post
- [ ] **On-page quality gate** — pipeline refuses to emit final Markdown if post scores below threshold (configurable, default 70/100); logs failures to `output/run_state/seo-failures.jsonl`
- [ ] **Technical SEO checker** — periodic crawl pipeline: checks all published URLs for broken internal links, missing canonical tags, duplicate titles/metas, missing sitemap entries, robots.txt blocking; outputs prioritised fix list to `output/technical-seo.md`
- [ ] **Core Web Vitals monitor** — fetches PageSpeed Insights API for top 10 pages monthly; flags any page scoring below 70 on mobile; saves trend data to `output/cwv-history.jsonl`

### Audit & observability pipeline

The real bottleneck isn't generating more content — it's that 60+ existing pages are "Crawled - currently not indexed". This sub-pipeline observes the live site, measures rejection signals, and feeds priorities back into the content stages so they fix what's broken instead of producing more.

Adds top-level `seo/data/` (date-keyed JSON snapshots per stage) and `seo/lib/{crawl,similarity,audit_state}.py`. Adds `beautifulsoup4` to `pyproject.toml`. Each stage is independently runnable via Make; chained by a top-level `make audit` target.

**Stage 1 — `crawl_site`**
- [ ] Fetch sitemap.xml, parse URL list, respect robots.txt
- [ ] Polite crawl: 0.5s delay + jitter, `User-Agent: hybridautopart-seo-bot/0.1 (+contact)`
- [ ] Per-URL capture: status, final_url, redirect chain, title, meta description, canonical, h1[], word_count, internal_links[], outbound_links[], images_without_alt
- [ ] Output: `data/crawls/YYYY-MM-DD.json` (one snapshot per day, idempotent)
- [ ] State: `output/run_state/status.jsonl` keyed by URL for resume mid-crawl
- [ ] New `lib/crawl.py`: RobotsChecker, RateLimiter, fetch_page, parse_page

**Stage 2 — `audit_technical`**
- [ ] Read latest `data/crawls/*.json`; emit issues per URL
- [ ] Output: `data/audits/technical/YYYY-MM-DD.json`

Per-page checks:
- [ ] HTTP status: 4xx/5xx and network errors (status==0)
- [ ] Redirect chain > 1 hop
- [ ] Missing title
- [ ] Title too short (<30 chars)
- [ ] Title too long (>60 chars)
- [ ] Missing meta description
- [ ] Thin meta description (<50 chars)
- [ ] Meta too long (>160 chars)
- [ ] Missing canonical
- [ ] Canonical mismatch (canonical != final_url, ignoring trailing slash)
- [ ] Missing H1
- [ ] Multiple H1s on one page
- [ ] Title/H1 mismatch (word overlap < 50%)
- [ ] Few internal links (< 3)
- [ ] Many outbound links (> 20)
- [ ] Images missing alt (count > 0)
- [ ] Cross-language slug references (SITE-SPECIFIC: `/blog/` vs `/blog-en/`)

Cross-page checks:
- [ ] Duplicate titles (same title used by multiple URLs)
- [ ] Duplicate meta descriptions
- [ ] Orphan pages (no inbound internal link from any other crawled page)

Deferred (out of scope for v1):
- Title-case violations — too easy to false-positive on brand/acronym terms
- Trailing-slash URL inconsistency — rare on WP
- Canonical points to non-2xx target — needs second-pass fetching of canonical URLs
- FAQ / Article schema presence — needs JSON-LD parsing, fits better as its own stage

**Stage 3 — `audit_content`**
- [ ] Read latest crawl; flag thin pages (<800 words, configurable)
- [ ] TF-IDF + cosine similarity across all pages; cluster pairs ≥0.75 as near-duplicates
- [ ] Detect title/H1 mismatch, missing H1
- [ ] Output: `data/audits/content/YYYY-MM-DD.json` (thin_pages, duplicate_clusters, title_h1_mismatch)
- [ ] New `lib/similarity.py`: TfidfVectorizer, cosine_matrix, cluster_by_threshold (stdlib, no sklearn)

**Stage 4 — `fetch_gsc` (CSV v1)**
- [ ] Read CSV exports from `data/gsc/inbox/` (queries.csv, pages.csv, coverage.csv)
- [ ] Normalize into unified JSON: queries with impressions/CTR/position, pages with index status (esp. "Crawled-not-indexed")
- [ ] Output: `data/gsc/YYYY-MM-DD.json`
- [ ] V2 (deferred — moved to V2 P3 "Search Console API integration"): swap CSV ingest for OAuth API fetch behind same output schema

**Stage 5 — `compare_runs`**
- [ ] Read today's + previous-existing-day audit + crawl + GSC
- [ ] Diff: new issues, resolved issues, regressions (page that was indexed but isn't now, page with impression loss >X%, new thin page)
- [ ] Output: `data/diffs/YYYY-MM-DD.json`

**Stage 6 — `triage`**
- [ ] Read all latest audit outputs; merge into a prioritized action feed
- [ ] Output: `data/triage/YYYY-MM-DD.json` + `data/triage/latest.json` pointer
- [ ] Buckets: `improve` (existing pages flagged thin/duplicate/not-indexed), `consolidate` (near-duplicate cluster merge candidates), `create` (GSC queries with impressions but no matching page), `fix` (technical issues)
- [ ] Also emits `reports/audit-YYYY-MM-DD.md` (human-readable summary)

**Integrations with existing stages**
- [ ] `generate_article_ideas`: new env `USE_TRIAGE=true` + `TRIAGE_FILE=../../data/triage/latest.json`. When triage exists, prepend `create` candidates to seed-keyword expansion. Backward-compatible (no triage → existing behavior).
- [ ] `revise_articles`: new env `CONTENT_AUDIT_FILE=../../data/audits/content/latest.json`. For articles whose slug is in `thin_pages` or any `duplicate_clusters` member, inject extra system-prompt directive ("flagged thin/near-duplicate of X — expand depth, differentiate from sibling") before review feedback.

**Top-level orchestration**
- [ ] `make audit` — run full chain (crawl → technical+content+gsc in parallel → compare → triage)
- [ ] `make audit-fast` — skip recrawl, reuse latest crawl snapshot (audits + diff + triage only)
- [ ] Update `seo/CLAUDE.md` with the new stages and `data/` layout

### Monetization
- [ ] Apply for Mediavine at 10K sessions/month
- [ ] Add RockAuto affiliate links to repair cost posts
- [ ] Launch email newsletter

---

## Phase 3 — Authority & Scale
Target: 10,000 → 100,000 visits/month

### Backlink strategy
- [ ] HARO responses: 2–3/week
- [ ] Resource page outreach: 5–10 emails/month
- [ ] Guest posts: 1–2/month on engineering/car sites

### Content scale
- [ ] Maintain 3 posts/week
- [ ] Used car buying guides by model year
- [ ] DIY repair guides with affiliate tool links
- [ ] Weekly hybrid car news roundup

### YouTube companion channel
- [ ] Launch "Hybrid Car Engineering" channel
- [ ] First video: PSD simulator animated explainer
- [ ] Target: 3–5 videos/month

### Revenue targets
- [ ] Mediavine display ads: $1,200/month at 100K visits
- [ ] Amazon Associates: $3,000/month
- [ ] Sponsored posts: $1,000/month
- [ ] Newsletter: $500/month

---

## V2 — WordPress Integration + Multi-site Expansion
**Status:** Planned — 1k–10k visits/month

Goal: remove manual steps from the pipeline and expand the content machine to other portfolio sites.

| Phase | Feature | Type | Status |
|-------|---------|------|--------|
| P1 | WordPress REST API — push drafts directly from pipeline output | Pipeline | [ ] |
| P1 | Auto-set Yoast meta, category, tags via WP API | Pipeline | [ ] |
| P1 | Auto-embed images into post body on upload | Pipeline | [ ] |
| P1 | Auto-insert internal links via WP API post search | Pipeline | [ ] |
| P2 | Per-site pipeline config (seo.env, persona, topics per domain) | Pipeline | [ ] |
| P2 | Apply content machine to iotbastion.com | Expansion | [ ] |
| P2 | Shared lib/, site-specific prompts and topic queue | Pipeline | [ ] |
| P2 | Unified `make all-sites` run across portfolio | Pipeline | [ ] |
| P3 | Search Console API integration — weekly auto-pull, flag quick wins | Intelligence | [ ] |
| P3 | Stale content detector — flag declining posts for refresh | Intelligence | [ ] |
| P3 | Automated content refresh pipeline | Pipeline | [ ] |
| P3 | Competitor gap monitor | Intelligence | [ ] |
| P3 | Weekly newsletter auto-draft from published posts | Pipeline | [ ] |

---

### Phase 1 — Automated WordPress Publishing
- [ ] WordPress REST API integration: push articles directly from pipeline output to WP drafts
- [ ] Auto-set Yoast SEO title + meta description via WP API on publish
- [ ] Auto-embed images into post body on upload
- [ ] Auto-assign category and tags from topic cluster field
- [ ] Auto-insert internal links using WP API post search
- [ ] Pipeline output: `DRAFT` in WordPress, not published — owner still reviews before going live

### Phase 2 — Multi-site Content Machine
- [ ] Parameterise pipelines per site (site-specific `seo.env`, persona, topic queue)
- [ ] Apply content machine to next portfolio site (iotbastion.com)
- [ ] Shared `lib/` across sites; site-specific `prompts/persona.txt` and `topics.json`
- [ ] Cross-site internal linking where topics overlap (hybrid tech ↔ IoT/embedded)
- [ ] Unified run dashboard: one `make all-sites` to queue content across portfolio

### Phase 3 — Content Intelligence
- [ ] Search Console API integration: auto-pull impression/CTR data weekly, flag quick wins
- [ ] Stale content detector: flag posts >6 months old with declining impressions for refresh
- [ ] Automated content refresh pipeline: feed old post + SC data → revised draft
- [ ] Competitor gap monitor: detect new competitor posts on tracked keywords
- [ ] Weekly newsletter auto-draft from the 3 posts published that week

---

## V3 — Full Automation + Productisation
**Status:** Speculative — 10k–100k visits/month

Goal: reduce owner time to near-zero for content operations; explore selling the machine.

| Phase | Feature | Type | Status |
|-------|---------|------|--------|
| P1 | Full publish pipeline — idea → draft → review → revise → WP, no manual steps | Pipeline | [ ] |
| P1 | Confidence scoring — auto-publish PASS, flag REVISE for owner | Pipeline | [ ] |
| P1 | YouTube script pipeline — top articles → video scripts | Channel | [ ] |
| P1 | AI thumbnail generation (DALL-E / Flux) | Channel | [ ] |
| P1 | Automated A/B title testing — winner promoted after 30 days | Growth | [ ] |
| P2 | Portfolio orchestration web UI — traffic, revenue, queue across all sites | Dashboard | [ ] |
| P2 | Cross-site backlink opportunity detector | Growth | [ ] |
| P2 | Automated affiliate performance tracking | Revenue | [ ] |
| P2 | Domain acquisition scoring tool | Expansion | [ ] |
| P3 | Package content machine as standalone product for niche site owners | Product | [ ] |
| P3 | Site onboarding — domain → persona + seeds + first 20 topics | Product | [ ] |
| P3 | Usage-based pricing — per article / per site | Product | [ ] |
| P3 | 3–5 beta users from niche site communities | Product | [ ] |

---

### Phase 1 — Zero-Touch Content Production
- [ ] Full publish pipeline: idea → draft → review → revise → WP draft, no manual steps
- [ ] Confidence scoring: auto-publish posts that score PASS in review; flag REVISE for owner
- [ ] YouTube script pipeline: convert top-performing articles to video scripts automatically
- [ ] AI thumbnail generation for YouTube videos (DALL-E / Flux)
- [ ] Automated A/B title testing: two title variants per post, winner promoted after 30 days

### Phase 2 — Portfolio Orchestration Dashboard
- [ ] Single web UI showing traffic, revenue, and content queue across all portfolio sites
- [ ] Cross-site backlink opportunity detector (site A post links to site B where relevant)
- [ ] Automated affiliate performance tracking: which posts earn, which don't
- [ ] Domain acquisition scoring: evaluate new domain opportunities against portfolio gaps

### Phase 3 — Productise the Machine
- [ ] Package content machine as a standalone tool for other niche site owners
- [ ] Site-specific onboarding: point at a domain, generate persona + seed keywords + first 20 topics
- [ ] Usage-based pricing: pay per article generated / per site connected
- [ ] Sell or license to 3–5 beta users from niche site communities (r/juststart, Niche Pursuits)
