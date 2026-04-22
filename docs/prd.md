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
| P2 | Mediavine application + email newsletter | Revenue | [ ] |
| P3 | Backlink strategy — HARO, outreach, guest posts | Growth | [ ] |
| P3 | Content scale — 144 posts + used car + DIY guides | Content | [ ] |
| P3 | YouTube companion channel | Channel | [ ] |
| P3 | Revenue at 100K — ads + affiliate + sponsored + newsletter | Revenue | [ ] |

---

## Phase 1 — Foundation & Recovery (Months 1–3)
Target: 833 → 3,000 visits/month

### Pipeline: dual-provider API support
- [ ] Add `call_llm(system, user, config)` to `lib/http.py` — auto-detects provider from `API_URL`
- [ ] Anthropic path: `x-api-key` header, `anthropic-version`, `{"system": ..., "messages": [...]}` request shape, `result["content"][0]["text"]` extraction
- [ ] OpenAI path: `Authorization: Bearer` header, `{"messages": [system, user]}` request shape, `result["choices"][0]["message"]["content"]` extraction
- [ ] All pipeline `generate_ai()` functions delegate to `call_llm` — no per-pipeline provider logic
- [ ] Switch provider by changing `API_URL` + `MODEL` + `API_KEY` in `seo.env` only
- [ ] Tests: mock both response shapes, assert correct extraction per provider

### Emergency fixes (Week 1)
- [ ] Remove Lamill Web Systems attribution from About Us sidebar
- [ ] Delete "Covers:" keyword spam from prius-pwr-mode
- [ ] Remove Subaru Crosstrek from Toyota PSD vehicle list (factual error)
- [ ] Fix broken `/blog/` → `/blog-en/` redirect in `.htaccess`
- [ ] Update footer © year to dynamic
- [ ] Fix H1/title mismatch on toyota-hybrid-synergy-drive-problems page

### Title & meta blitz (Week 1–2)
- [ ] Rewrite SEO titles + H1s for all 8 top pages
- [ ] Paste all 25 prepared meta descriptions into Yoast

### Schema & structure (Week 2–3)
- [ ] Enable Yoast breadcrumbs + Article schema
- [ ] Create 5 topic categories; reassign all 46 posts
- [ ] Add FAQ schema JSON-LD to top 8 posts

### Content expansion (Week 3–4)
- [ ] Expand prius-pwr-mode to 2,800 words (ECO/PWR table, Gen 5 section)
- [ ] Expand toyota-prius-power-split-device to 3,500 words (Willis equation, 6 operating modes)
- [ ] Expand prius-0-60 with complete model-year table 2001–2024

### Content velocity begins (Month 2)
- [ ] Set up Amazon Associates affiliate account
- [ ] Add affiliate links to top 5 existing posts
- [ ] Launch 12 new posts (3/week) — see topic queue in `seo/topics.json`

### PSD Simulator launch (Month 3)
- [ ] Complete React plugin build and deploy to WordPress
- [ ] Write dedicated "PSD Simulator" post
- [ ] Execute launch outreach (r/prius, r/Toyota, LinkedIn, PriusChat)

---

## Phase 2 — Content Machine (Months 4–12)
Target: 3,000 → 10,000 visits/month

### Toyota hybrid model expansion
- [ ] RAV4 Hybrid: 12-post cluster (Month 4)
- [ ] Camry Hybrid + battery deep-dive cluster (Month 5)
- [ ] Corolla Hybrid + featured snippet targeting (Month 6)
- [ ] Highlander Hybrid + family comparison content (Month 7)
- [ ] Prius Prime + EV/PHEV content (Month 8)

### Interactive tools (Month 9)
- [ ] Hybrid vs Gas Savings Calculator (React plugin)
- [ ] Hybrid Battery Health Estimator (React plugin)
- [ ] Toyota Hybrid Model Comparison Tool (React plugin)

### Cross-linking pipeline (Month 5)
- [ ] Crawl all published posts and pages; build a keyword → URL index
- [ ] For each post, identify 5–10 outbound link opportunities to other site content based on semantic overlap
- [ ] Output: `output/cross-links.md` — per-post table of suggested anchor text + target URL + insertion point (nearest heading)
- [ ] Optional: WP REST API mode — insert links directly into post body as HTML in WordPress drafts

### Provider comparison — Claude vs OpenAI (Month 5)
- [ ] Run `write_articles` on the same 5 topics twice — once with `claude-sonnet-4-6`, once with `gpt-4.1-mini`
- [ ] Score both outputs with `review_articles` pipeline (HCU, structure, engagement scores)
- [ ] Manual review: engineering depth, factual accuracy, word quality
- [ ] Decision output: preferred provider per use-case (long-form vs short, commercial vs informational)
- [ ] Set winning provider as default in `seo.env`; keep loser available as override

### SEO checker pipelines (Month 6)
- [ ] **Per-post SEO checker** — runs automatically after `revise_articles`; scores each post against: title length (50–60 chars), meta description present (145–160 chars), primary keyword in first 100 words, at least 3 internal links, FAQ schema present, word count ≥ target; outputs `seo-score.json` per post
- [ ] **On-page quality gate** — pipeline refuses to emit final Markdown if post scores below threshold (configurable, default 70/100); logs failures to `output/run_state/seo-failures.jsonl`
- [ ] **Technical SEO checker** — periodic crawl pipeline: checks all published URLs for broken internal links, missing canonical tags, duplicate titles/metas, missing sitemap entries, robots.txt blocking; outputs prioritised fix list to `output/technical-seo.md`
- [ ] **Core Web Vitals monitor** — fetches PageSpeed Insights API for top 10 pages monthly; flags any page scoring below 70 on mobile; saves trend data to `output/cwv-history.jsonl`

### Monetization
- [ ] Apply for Mediavine at 10K sessions/month
- [ ] Add RockAuto affiliate links to repair cost posts
- [ ] Launch email newsletter (Month 6)

---

## Phase 3 — Authority & Scale (Months 13–24)
Target: 10,000 → 100,000 visits/month

### Backlink strategy
- [ ] HARO responses: 2–3/week
- [ ] Resource page outreach: 5–10 emails/month
- [ ] Guest posts: 1–2/month on engineering/car sites

### Content scale
- [ ] Maintain 3 posts/week (144 posts in months 13–24)
- [ ] Used car buying guides by model year
- [ ] DIY repair guides with affiliate tool links
- [ ] Weekly hybrid car news roundup

### YouTube companion channel (Month 15+)
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
