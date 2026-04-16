# hybridautopart.com — Full SEO Audit & Action Plan
**Date:** April 15, 2026
**Analyst:** Claude (Anthropic) — based on live site crawl + Search Console data
**Owner:** Vik Thomas / Lamill Web Systems

---

## Executive Summary

| Metric | Current | Target (12 months) |
|--------|---------|-------------------|
| Annual visits | ~10,000 | 100,000 |
| Monthly visits | ~833 | ~8,300 |
| Annual impressions | 399,000 | 800,000+ |
| Average CTR | 0.5% | 3–5% |
| Average position | 18.7 | 8–12 |
| Monetization | $0 | $500–1,500/mo |

**Site health score: 42/100**

The site is in recovery from Google's Helpful Content Update (Aug 2022). The good news: 399K impressions proves Google still knows this site exists and covers real topics people search for. The problem is almost entirely CTR and content depth — not discoverability. This is fixable without starting over.

**Top 3 highest-impact actions:**
1. Fix title tags on 5 high-impression pages (48–69K impressions each, under 0.5% CTR) — 30 min work, could add 800–1,500 clicks/month immediately
2. Delete keyword stuffing ("Covers:" lists) from all posts — direct HCU compliance fix
3. Add FAQ schema to all posts with FAQ sections — 3x screen real estate in Google results without moving up a single position

---

## 1. Traffic Analysis

### 12-Month Overview (April 2025 – April 2026)
- **Total clicks:** 1,860
- **Total impressions:** 399,000
- **CTR:** 0.5% (industry average for position 5 is ~7%, position 1 is 25–30%)
- **Average position:** 18.7 (mostly page 2)
- **Indexed pages:** 69 (8 pages of posts)
- **Unique queries in Search Console:** 1,000+

### Traffic History
| Year | Visits |
|------|--------|
| 2020 | ~2,000 (early) |
| 2021 | ~35,000 |
| 2022 | ~45,000 (peak) |
| 2023 | ~20,000 (HCU hit) |
| 2024 | ~12,000 |
| 2025 | ~10,000 |
| 2026 (proj) | ~10,000 (flat without action) |

**Root cause of drop:** Google Helpful Content Update August 2022 + reinforcement September 2023. The site's content was flagged as not demonstrating sufficient first-hand expertise or depth. Generic explanatory content written without personal experience or engineering insight is the specific pattern being penalized.

---

## 2. Top Pages Analysis

### Page 1: toyota-prius-power-split-device
| Metric | Value |
|--------|-------|
| Impressions/yr | 57,724 |
| Clicks/yr | 723 |
| CTR | 1.3% |
| Est. position | 12–15 |
| Word count | ~1,200 |

**Issues found:**
- Title is lowercase: "Toyota Power Split **device**" — unprofessional
- Content reads like Wikipedia summary — no engineering voice
- Subaru Crosstrek listed as Toyota PSD vehicle — **factual error**
- Broken internal link: uses `/blog/` prefix instead of `/blog-en/`
- 31-item Wikipedia link list adds no value and bleeds page authority
- No FAQ schema despite having FAQ section
- Footer shows © 2022 — stale trust signal
- No "Last Updated" date
- Only 1 internal link (at very bottom)

**Current title:** Toyota Power Split device
**Recommended title:** Toyota Prius Power Split Device Explained (With Interactive Diagram)
**Meta description:** The Power Split Device is the heart of every Toyota hybrid — a planetary gear system splitting power between the engine, MG1, and MG2. Full visual guide with diagram.

**Missing content sections:**
- Actual planetary gear math (Willis equation) — your engineering advantage
- Operating modes breakdown (6 distinct modes: start, EV low, normal, full accel, regen, highway)
- Common PSD failure symptoms (P3125 code, bearing noise, oil contamination)
- PSD differences across Prius generations
- Interactive simulator (in development)

**Priority: CRITICAL — your #1 page by clicks, fix immediately**

---

### Page 2: prius-pwr-mode
| Metric | Value |
|--------|-------|
| Impressions/yr | 69,904 |
| Clicks/yr | 203 |
| CTR | 0.3% |
| Est. position | 15–18 |
| Word count | ~1,465 |

**Issues found (crawled live):**
- Keyword stuffing at top: "Covers: pwr mode prius, power mode prius, prius power mode" — **delete immediately**
- Same YouTube video embedded twice — duplicate content signal
- H1 not updated to match new Yoast SEO title
- No FAQ schema despite having detailed FAQ section
- About Us sidebar: "Lamill Web Systems creates content" — E-E-A-T damage
- No "Last Updated" date
- Only 1 internal link

**Current title:** Prius Power Mode: What It Does (PWR Mode Explained + When To Use It)
**Recommended title:** What Does PWR Mode Do in a Prius? (Pros, Cons & When to Use It)
**Meta description:** PWR mode makes your Prius throttle more aggressive — but does it hurt fuel economy? Learn exactly what it does, when to use it, and whether it's worth switching on.

**Missing content sections:**
- Fuel economy comparison table: ECO vs Normal vs PWR (with real numbers)
- Gen 5 (2023+) and Prius Prime PWR mode activation
- Does PWR mode drain battery faster? (direct question from search data)

**Priority: CRITICAL — highest impressions on site (69K), 0.3% CTR**

---

### Page 3: prius-0-60
| Metric | Value |
|--------|-------|
| Impressions/yr | 48,143 |
| Clicks/yr | 52 |
| CTR | 0.1% |
| Est. position | 18–22 |

**Issues found:**
- CTR of 0.1% is the worst on the entire site — 48K people saw this in Google and only 52 clicked
- Title previously: "How Fast Can A Prius Go 0-60? (From 0 To 60?)" — redundant phrasing
- Content has good infographic with model year data
- Missing: complete model-year table with all generations (Gen 1 through Gen 5)
- Missing: comparison to similar cars (Camry Hybrid, Corolla Hybrid, Honda Civic Hybrid)

**Updated title (already applied):** Prius 0-60 Times: Every Model Year Compared (2001–2024)
**Meta description:** How fast is your Prius? See 0-60 mph times for every Prius generation from 2001 to 2024 — Gen 1 through Gen 4, plug-in, and Prime. Includes real-world test results.

**Missing content:**
- Complete model year table (2001–2024) — currently only shows select years via infographic
- 0-60 in PWR mode vs Normal mode comparison
- How Prius compares to other hybrids on acceleration

**Priority: HIGH — biggest CTR upside on site**

---

### Page 4: guide-to-ev-mode-in-prius
| Metric | Value |
|--------|-------|
| Impressions/yr | 25,241 |
| Clicks/yr | 51 |
| CTR | 0.2% |

**Recommended title:** Prius EV Mode: How to Activate It, When It Works & Its Limits
**Meta description:** EV mode lets your Prius run silently on battery only — but it only works under 25 mph. Here's how to activate it, maximize range, and why it sometimes won't engage.

**Missing content:**
- Why EV mode sometimes won't activate (battery temp, SoC threshold)
- EV mode by generation (Gen 3 button vs Gen 4 drive mode selector)
- How long can you stay in EV mode? (distance/time limits)

**Priority: HIGH**

---

### Page 5: phev-vs-fhev
| Metric | Value |
|--------|-------|
| Impressions/yr | 33,113 |
| Clicks/yr | 327 |
| CTR | 1.0% |

**Recommended title:** FHEV vs PHEV: Key Differences, Real-World Range & Which to Buy
**Meta description:** FHEV can't plug in. PHEV can. Compare full hybrid vs plug-in hybrid on real-world range, fuel savings, charging costs, and which type suits your daily driving.

**Missing content:**
- Cost comparison table (purchase price, fuel savings, charging cost)
- Real-world range figures for top PHEV and FHEV models
- "Which should I buy?" decision section based on commute distance

**Priority: MEDIUM-HIGH — already decent CTR, room to grow**

---

### Page 6: what-is-pzev (what-is-gzev)
| Metric | Value |
|--------|-------|
| Impressions/yr | 23,900 |
| Clicks/yr | 62 |
| CTR | 0.3% |

**Note:** URL slug says "gzev" but content is about PZEV — URL/content mismatch may be confusing Google.

**Recommended title:** What Is a PZEV? (Partial Zero Emission Vehicle Explained Simply)
**Meta description:** PZEV means Partial Zero Emission Vehicle — a cleaner gas car meeting strict California standards. Learn what it means, which cars qualify, and how it differs from a hybrid.

**Priority: MEDIUM**

---

### Page 7: toyota-hybrid-synergy-drive-problems
| Metric | Value |
|--------|-------|
| Impressions/yr | 10,364 |
| Clicks/yr | 80 |
| CTR | 0.8% |

**Critical mismatch:** URL says "problems" but H1 says "What Is Toyota Hybrid Synergy Drive? (Simple Explanation)" — Google is ranking this for problem queries but the title signals an explainer. Fix immediately.

**Recommended title:** Toyota Hybrid Synergy Drive Problems: Most Common Issues & Fixes
**Meta description:** The most common Toyota Hybrid Synergy Drive problems: battery degradation, MG1/MG2 failures, and inverter issues. Learn the warning signs early and what repairs cost.

**Priority: MEDIUM-HIGH — title/URL mismatch is actively hurting this page**

---

## 3. Technical SEO Issues

### Critical
| Issue | Impact | Fix |
|-------|--------|-----|
| No FAQ schema | Missing rich results (3x screen space) | Enable in Yoast or add JSON-LD manually |
| No Article schema | Posts not recognized as articles by Google | Yoast → Search Appearance → Content Types |
| No breadcrumbs | Missing in search results | Yoast → Search Appearance → Breadcrumbs → Enable |
| All posts in "Blog" category | No topical authority signals | Create 5 categories, reassign posts |
| Duplicate link tags in sidebar | Confuses Google crawler | Fix theme template (Recent Content widget) |
| Footer © 2022 | Stale trust signal | Dynamic year in footer.php |

### Important
| Issue | Impact | Fix |
|-------|--------|-----|
| No "Last Updated" dates | Freshness signal missing | Add to post template + Yoast schema |
| About Us: "Lamill Web Systems creates content" | E-E-A-T damage | Rewrite to highlight Vik's engineering expertise |
| No Open Graph images | Poor social sharing preview | Add OG image to each post in Yoast Social tab |
| hreflang not configured | French post confusing Google | Add hreflang or remove French post |

### Minor
| Issue | Impact | Fix |
|-------|--------|-----|
| Keyword "Covers:" lists in posts | HCU penalty signal | Delete from all posts |
| Duplicate YouTube embeds | Quality signal | Remove duplicate from pwr-mode post |
| Factual error: Subaru in PSD list | E-E-A-T damage | Remove item #31 from PSD page |
| Broken internal link on PSD page | Crawl error | Change /blog/ to /blog-en/ |

---

## 4. E-E-A-T Assessment

| Dimension | Score | Issues |
|-----------|-------|--------|
| Experience | 3/10 | Content rarely mentions personal experience with hybrid vehicles |
| Expertise | 4/10 | Author bio doesn't mention embedded engineering background |
| Authoritativeness | 3/10 | No external citations, no author credentials visible |
| Trustworthiness | 4/10 | Stale copyright, generic About Us, factual error on PSD page |
| **Overall** | **3.5/10** | **Primary reason for HCU penalty** |

**Key fix:** Add to author bio on /author/vik/: "Vik Thomas is an embedded systems engineer with 10+ years of experience in motor control and automotive systems. He owns and drives Toyota hybrids and writes about them from an engineering perspective."

---

## 5. Content Gap Opportunities

Based on 1,000+ Search Console queries, these represent the highest-value untapped topics:

| Cluster | Est. monthly searches | Existing page? | Action |
|---------|----------------------|----------------|--------|
| PWR mode fuel economy | 3,000+ | Partial | Expand pwr-mode page |
| FHEV meaning / definition | 4,000+ | Partial | Add dedicated FHEV page |
| Prius models by year | 2,500+ | No | New page |
| PSD simulator | 1,200+ | Building | Complete simulator |
| Hybrid synergy drive problems | 2,000+ | Yes (weak) | Expand |
| Prius Prime EV range | 3,500+ | No | New page |
| RAV4 Hybrid PWR mode | 5,000+ | No | New page (expansion) |
| Prius transmission problems | 1,800+ | No | New page |
| How long do hybrid batteries last | 8,000+ | No | New page |
| Toyota hybrid battery replacement cost | 6,000+ | No | New page |

**Biggest missed opportunity:** "How long do hybrid batteries last" and "Toyota hybrid battery replacement cost" are 2 of the highest-volume hybrid queries with commercial intent. These bring in readers who are close to a repair or purchase decision — highest value for affiliate links.

---

## 6. Monetization Readiness

**Current state:** $0/month
**Blocker:** Traffic too low for most ad networks. Need 10K sessions/month minimum for Mediavine.

### Affiliate links (can add NOW — no traffic threshold)
These can be added immediately to existing posts:

| Post | Affiliate opportunity | Network | Est. commission |
|------|-----------------------|---------|-----------------|
| PSD page | Toyota hybrid batteries, OBD2 scanners | Amazon | 3-4% |
| PWR mode page | OBD2 scanners, Prius accessories | Amazon | 3-4% |
| 0-60 page | Performance parts, tires | Amazon/RockAuto | 3-8% |
| PHEV vs FHEV | Charging cables, EV accessories | Amazon | 3-4% |
| Battery page (new) | Hybrid battery replacement, mechanics | Direct/Amazon | High |

**Recommended affiliate setup:**
1. Join Amazon Associates (free, instant approval)
2. Add 3-5 contextual affiliate links per post — not in sidebars, within content
3. Add disclosure banner (legally required)
4. Target: $50-100/month within 3 months at current traffic

### Ad network timeline
| Traffic milestone | Network | Est. monthly revenue |
|------------------|---------|---------------------|
| 10K sessions/mo | Ezoic | $50-150 |
| 10K sessions/mo | Mediavine | $200-600 |
| 50K sessions/mo | Mediavine | $1,000-3,000 |
| 100K sessions/mo | Mediavine | $3,000-8,000 |

---

## 7. Priority Action List

### Do today (under 2 hours total)

1. **Delete "Covers:" keyword list from prius-pwr-mode** — 2 min
   - Open post → delete the "Covers: pwr mode prius..." bullet section
   - This is active HCU bait

2. **Remove duplicate YouTube embed from prius-pwr-mode** — 2 min
   - Find and delete second instance of the Toyota 0-60 video

3. **Remove Subaru Crosstrek from PSD vehicles list** — 2 min
   - Item #31 in the numbered list on toyota-prius-power-split-device page

4. **Fix broken internal link on PSD page** — 2 min
   - Change href from `/blog/how-does-a-prius-transmission-work/` to `/blog-en/prius-transmission-work/`

5. **Update footer copyright year** — 5 min
   - In WordPress → Appearance → Theme Editor → footer.php
   - Replace hardcoded 2022 with `<?php echo date('Y'); ?>`

6. **Fix H1/title mismatch on HSD problems page** — 5 min
   - Change H1 from "What Is Toyota Hybrid Synergy Drive? (Simple Explanation)"
   - To: "Toyota Hybrid Synergy Drive Problems: Most Common Issues & Fixes"

7. **Update About Us sidebar** — 10 min
   - Replace "Lamill Web Systems creates the content" with author expertise bio

### This week (4-6 hours total)

8. **Enable Yoast breadcrumbs** — 15 min
   - Yoast → Search Appearance → Breadcrumbs → Enable
   - Add shortcode/function to single.php above post title

9. **Enable Article schema in Yoast** — 10 min
   - Yoast → Search Appearance → Content Types → Posts → Schema → Article

10. **Create 5 WordPress categories** — 30 min
    - Toyota Prius Guides
    - Hybrid System Explained
    - PHEV & EV Guides
    - Hybrid Car Comparisons
    - Hybrid Car Buying
    - Reassign all 46 posts

11. **Add FAQ schema to top 5 posts** — 60 min
    - prius-pwr-mode, PSD page, prius-0-60, phev-vs-fhev, ev-mode-in-prius
    - Use Yoast FAQ blocks or add JSON-LD manually

12. **Add internal links across top 10 posts** — 60 min
    - Each post should link to at least 3 other relevant posts
    - PSD page → PWR mode, EV mode, Prius transmission
    - PWR mode page → PSD, 0-60, EV mode

13. **Add "Last Updated: April 2026" to top 10 posts** — 30 min
    - Add above/below byline on each post
    - Update any outdated information in those posts

14. **Update author bio at /author/vik/** — 20 min
    - Add: embedded systems engineer, motor control experience, hybrid car owner
    - Add photo if possible

### This month (content work)

15. **Expand prius-pwr-mode with fuel economy data** — 3 hrs
    - Add ECO vs Normal vs PWR comparison table with real MPG numbers
    - Add Gen 5 (2023+) and Prius Prime activation instructions
    - Update word count from 1,465 to 2,500+

16. **Expand PSD page with engineering depth** — 4 hrs
    - Rewrite opening paragraph to lead with the answer
    - Add Willis equation section with actual gear math
    - Add 6 operating modes with power flow descriptions
    - Add common failure symptoms section
    - Replace Wikipedia list with clean table

17. **Add model-year table to prius-0-60** — 2 hrs
    - Complete table: 2001–2024 with 0-60, hybrid type, engine
    - Add PWR mode vs Normal mode comparison

18. **Write new post: "How Long Do Hybrid Batteries Last?"** — 3 hrs
    - Target: highest-volume untapped query
    - Include: Toyota warranty, real-world data, replacement cost, signs of degradation
    - Add Amazon affiliate links to battery testers

19. **Write new post: "Toyota Hybrid Battery Replacement Cost"** — 3 hrs
    - High commercial intent — close to purchase/repair decision
    - Include: DIY vs dealer, gen-by-gen cost breakdown, refurbished options

20. **Deploy PSD simulator** — ongoing
    - Complete React plugin (in development)
    - Embed on PSD page
    - Promote on r/prius, PriusChat, LinkedIn

### Ongoing (weekly)

21. **Publish 2 posts/week** targeting Search Console query gaps
22. **Share each post** on r/prius, r/Toyota, r/electricvehicles
23. **Check Search Console weekly** — monitor CTR improvements post title fixes
24. **Add affiliate links** to every new post at time of writing

---

## 8. Traffic Recovery Forecast

| Timeline | Action | Expected traffic |
|----------|--------|-----------------|
| Week 1-2 | Title fixes + delete keyword stuffing | +200-400 clicks/mo |
| Month 1 | All quick fixes + FAQ schema | +500-800 clicks/mo |
| Month 3 | Content expansions + new posts | 2,000-3,000/mo |
| Month 6 | Simulator live + consistent publishing | 4,000-6,000/mo |
| Month 12 | Full content library + authority building | 8,000-12,000/mo |

**Conservative 10x estimate: 12-18 months**
**Aggressive 10x estimate: 9-12 months** (with 2 posts/week + simulator)

---

*Report generated: April 15, 2026*
*Based on: live site crawl, Search Console data (12 months), Jetpack stats (yearly)*
*Next audit recommended: July 2026*
