# PRD — hybridautopart.com Content Machine

---

## V1 — Content Machine for hybridautopart.com
**Status:** Live — real SEO traffic, <1k visits/month

## Phase 1 — Foundation & Recovery (Months 1–3)
Target: 833 → 3,000 visits/month

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
**Status:** Planned — begins after Phase 2 traffic milestone (10K visits/month)

Goal: remove manual steps from the pipeline and expand the content machine to other portfolio sites.

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
**Status:** Speculative — begins after 100K visits/month milestone

Goal: reduce owner time to near-zero for content operations; explore selling the machine.

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
