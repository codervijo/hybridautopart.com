# SEO Audit & Improvement Pipeline
# hybridautopart.com — Autonomous Background Agent
#
# HOW TO RUN (pick one):
#   cat SEO_PIPELINE_PROMPT.md | claude --dangerously-skip-permissions --print > seo-run.log 2>&1 &
#   claude --dangerously-skip-permissions "$(cat SEO_PIPELINE_PROMPT.md)" > seo-run.log 2>&1 &
#
# CHECK PROGRESS:
#   tail -f seo-run.log
#
# RESULTS IN THE MORNING:
#   cat seo-output/SUMMARY_REPORT.md
#   cat seo-output/ACTION_LIST.md

You are an autonomous SEO improvement agent for hybridautopart.com.
Run ALL tasks below sequentially without stopping for confirmation.
If a fetch fails, log the error and continue — do not stop the pipeline.
Save all outputs to ./seo-output/ directory.
Log every action to ./seo-output/pipeline.log with timestamps.

---

## SITE CONTEXT

URL: https://hybridautopart.com
Niche: Toyota Prius / hybrid vehicles
Owner: Vik Thomas — embedded systems / motor control engineer with genuine expertise
Platform: WordPress 6.5, Yoast SEO (free)
Current traffic: ~833 visits/month (10K/year)
Impressions: 399K/year, 0.5% CTR, avg position 18.7
Goal: 10K visits/month in 12 months, 100K/month in 24 months
Root cause of decline: Google Helpful Content Update Aug 2022 + Sept 2023

## KNOWN ISSUES (confirmed in prior audit)
1. "Covers: [keywords]" bullet spam at top of prius-pwr-mode — delete immediately
2. Duplicate YouTube embed in prius-pwr-mode post
3. Footer shows © 2022 — stale trust signal
4. "Recent Content" sidebar outputs duplicate "link to [Title]" anchor tags — theme bug
5. About Us says "Lamill Web Systems creates content" — E-E-A-T damage
6. All 46 posts in single "Blog" category — no topical clusters
7. No breadcrumbs enabled (Yoast supports this natively)
8. No FAQ schema on any posts despite many having FAQ sections
9. No Article schema on blog posts
10. No "Last Updated" dates visible on posts
11. Subaru Crosstrek incorrectly listed as Toyota PSD vehicle (item #31) — factual error
12. Broken internal link on PSD page: /blog/ prefix should be /blog-en/
13. H1 and SEO title mismatch on toyota-hybrid-synergy-drive-problems page
14. prius-0-60 has 48K impressions but 0.1% CTR — worst on site

## TOP PAGES (confirmed from Search Console)
- /blog-en/prius-pwr-mode/                      69,904 impr, 203 clicks, 0.3% CTR
- /blog-en/toyota-prius-power-split-device/      57,724 impr, 723 clicks, 1.3% CTR
- /blog-en/prius-0-60/                           48,143 impr,  52 clicks, 0.1% CTR
- /blog-en/guide-to-ev-mode-in-prius/            25,241 impr,  51 clicks, 0.2% CTR
- /blog-en/what-is-pzev/                         23,900 impr,  62 clicks, 0.3% CTR
- /blog-en/phev-vs-fhev/                         33,113 impr, 327 clicks, 1.0% CTR
- /blog-en/toyota-hybrid-synergy-drive-problems/ 10,364 impr,  80 clicks, 0.8% CTR
- /blog-en/subaru-phev-guide/                     4,535 impr,  37 clicks, 0.8% CTR
- /blog-en/prius-transmission-work/               9,141 impr,  41 clicks, 0.4% CTR

## ALREADY APPROVED TITLE REWRITES (apply these exactly)
- prius-0-60 → "Prius 0-60 Times: Every Model Year Compared (2001–2024)"
- prius-pwr-mode → "What Does PWR Mode Do in a Prius? (Pros, Cons & When to Use It)"
- guide-to-ev-mode-in-prius → "Prius EV Mode: How to Activate It, When It Works & Its Limits"
- what-is-pzev → "What Is a PZEV? (Partial Zero Emission Vehicle Explained Simply)"
- phev-vs-fhev → "FHEV vs PHEV: Key Differences, Real-World Range & Which to Buy"
- toyota-hybrid-synergy-drive-problems → "Toyota Hybrid Synergy Drive Problems: Most Common Issues & Fixes"
- toyota-prius-power-split-device → "Toyota Prius Power Split Device Explained (How It Actually Works)"
- subaru-phev-guide → "Subaru PHEV Guide: Models, Range, Charging & Is It Worth It? (2026)"

---

## PIPELINE TASKS — RUN ALL IN ORDER, NO STOPS

### TASK 0 — Setup
```bash
mkdir -p seo-output/crawl
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline started" > seo-output/pipeline.log
```

---

### TASK 1 — Crawl all top pages

Fetch each URL. For pages that load successfully, extract and save:
- Full page content → seo-output/crawl/[slug].txt
- Structured data → seo-output/crawl/[slug]-summary.json

JSON structure per page:
```json
{
  "url": "...",
  "title_tag": "...",
  "h1": "...",
  "meta_description": "...",
  "word_count": 0,
  "headings": ["H2: ...", "H3: ..."],
  "internal_links": ["url1", "url2"],
  "images_without_alt": 0,
  "has_faq_section": true,
  "has_keyword_stuffing": true,
  "has_last_updated": false,
  "issues_found": ["list of issues"]
}
```

Pages to crawl:
- https://hybridautopart.com (homepage)
- https://hybridautopart.com/blog-en/prius-pwr-mode/
- https://hybridautopart.com/blog-en/toyota-prius-power-split-device/
- https://hybridautopart.com/blog-en/prius-0-60/
- https://hybridautopart.com/blog-en/guide-to-ev-mode-in-prius/
- https://hybridautopart.com/blog-en/what-is-pzev/
- https://hybridautopart.com/blog-en/phev-vs-fhev/
- https://hybridautopart.com/blog-en/toyota-hybrid-synergy-drive-problems/
- https://hybridautopart.com/blog-en/subaru-phev-guide/
- https://hybridautopart.com/blog-en/prius-transmission-work/
- https://hybridautopart.com/blog-en/prius-generations/
- https://hybridautopart.com/author/vik/

Log: "[timestamp] Crawled [url] — [word_count] words, [issue_count] issues found"
If fetch fails: log "[timestamp] FAILED to fetch [url] — [error]" and continue.

---

### TASK 2 — CTR gap analysis

For each crawled page, calculate:
- Monthly impressions (from data above / 12)
- Current monthly clicks
- Clicks at 3% CTR (realistic page-2 improvement target)
- Clicks at 10% CTR (page-1 target)
- Monthly clicks being lost vs 3% CTR target
- Fix type: "title only" (30 min) / "title + content" (2 hrs) / "new page needed"

Output: seo-output/ctr-analysis.md

Format:
```
# CTR Gap Analysis

| Page | Monthly impr | Current clicks | At 3% CTR | Lost clicks/mo | Fix type | Priority |
|------|-------------|----------------|-----------|----------------|----------|----------|
...

## Total lost clicks per month at 3% CTR: [X]
## Total lost clicks per month at 10% CTR: [X]
## Quick win (title fixes only, this week): [X] clicks/mo recoverable
```

---

### TASK 3 — Full content audit per page

For each successfully crawled page, audit against these criteria:

**HCU compliance checklist:**
- [ ] No keyword stuffing (no "Covers:" lists, no unnatural repetition)
- [ ] Answers the question in first 100 words
- [ ] Written from first-person / experience perspective (not generic "we")
- [ ] Contains original data, insight, or personal experience
- [ ] No factual errors

**Content depth checklist:**
- [ ] Has a comparison table (where applicable)
- [ ] Has a FAQ section with 5+ questions
- [ ] Has "Last Updated" date
- [ ] Links to 3+ related internal pages
- [ ] Word count 2,000+ for main topic pages
- [ ] Has at least one image with descriptive alt text

**Technical checklist:**
- [ ] H1 matches or is very close to SEO title
- [ ] Primary keyword appears in first 100 words
- [ ] URL slug matches topic

Output: seo-output/content-audit.md

Format per page:
```
### /blog-en/[slug]/

**HCU issues:**
- [list]

**Content gaps:**
- [list]

**Technical issues:**
- [list]

**Recommended additions:**
- [section name]: [brief description] (~[word count] words)

**Priority:** Critical / High / Medium / Low
**Estimated fix time:** [X hours]
```

---

### TASK 4 — Generate optimized meta descriptions

For every page crawled, generate an optimized meta description if:
- Current meta is missing, OR
- Current meta is under 100 characters, OR
- Current meta doesn't include the primary keyword

Rules:
- 145-160 characters
- Include primary keyword naturally
- Include a click trigger (number, question, benefit, urgency)
- Match search intent exactly
- No clickbait — must accurately describe the page

Also flag: any page where H1 ≠ SEO title (mismatch hurts rankings)

Output: seo-output/meta-descriptions.md

Format:
```
### /blog-en/[slug]/
**Current meta:** "[text]" ([X] chars) — [OK / TOO SHORT / MISSING]
**Primary keyword:** [keyword]
**Recommended meta:** "[text]" ([X] chars)
**H1/Title mismatch:** YES → H1 is "[x]", title is "[y]" | NO
```

---

### TASK 5 — FAQ schema generator

For each page that has a FAQ section (detected in crawl):
1. Extract all Q&A pairs from the page
2. Generate valid JSON-LD FAQ schema
3. Note: schema should be added as HTML block in WordPress editor

Output: seo-output/faq-schema.md

Format per page:
```
### /blog-en/[slug]/
**Questions found:** [X]

**JSON-LD to add (paste as HTML block in WordPress):**
\`\`\`html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[question]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[answer]"
      }
    }
  ]
}
</script>
\`\`\`
```

---

### TASK 6 — Internal linking opportunity map

Based on all crawled pages:
1. List every page and how many inbound internal links it has
2. Flag orphan pages (0-1 inbound links)
3. Generate specific link opportunities: FROM page → TO page → suggested anchor text

Rules for good internal links:
- Link from high-traffic pages to lower-traffic related pages
- Use descriptive anchor text (not "click here")
- Only suggest contextually natural links

Output: seo-output/internal-links.md

Format:
```
## Pages by inbound internal links
| Page | Inbound links | Status |
|------|--------------|--------|
...

## Orphan pages (need links urgently)
...

## Specific link opportunities
| From page | To page | Suggested anchor text | Where to add |
|-----------|---------|----------------------|--------------|
...
```

---

### TASK 7 — New content opportunity report

Based on the known Search Console query data, generate content briefs for the 10 highest-value missing pages.

High-value query clusters to target:
- "how long do hybrid batteries last" — 8,000+ monthly searches
- "toyota hybrid battery replacement cost" — 6,000+
- "prius prime ev range real world" — 3,500+
- "rav4 hybrid pwr mode" — 3,000+
- "fhev meaning" / "what does fhev mean" — 4,000+
- "prius models by year" — 2,500+
- "hybrid battery degradation" — 2,000+
- "best obd2 scanner for prius" — 1,800+
- "prius transmission problems" — 1,800+
- "toyota hybrid vs honda hybrid reliability" — 1,500+

For each, generate a full content brief:

Output: seo-output/content-briefs.md

Format per brief:
```
### [Post title]

**Target keyword:** [primary keyword]
**Secondary keywords:** [2-3 related]
**Search intent:** Informational / Commercial / Transactional
**Est. monthly searches:** [X]
**Competition level:** Low / Medium / High
**Affiliate opportunity:** [product + network]
**Internal links to include:** [3-4 existing pages]
**Estimated word count:** [X]

**Outline:**
- H1: [title]
- Intro (answer in 2-3 sentences)
- H2: Quick Answer
- H2: [Section 1]
  - H3: [subsection]
- H2: [Section 2]
- H2: [Comparison table: X vs Y]
- H2: FAQ (list 6-8 questions)
- H2: Conclusion + next steps

**Opening paragraph draft:**
[Write a 75-word opening that directly answers the query and includes the primary keyword]
```

---

### TASK 8 — Technical SEO checklist

Fetch homepage and check the following. Flag PASS or FAIL with fix instructions for each FAIL.

Checks:
- HTTPS working (redirect from http://)
- Viewport meta tag present
- Canonical tag on homepage
- XML sitemap accessible at /sitemap.xml or /sitemap_index.xml
- Robots.txt accessible and not blocking Googlebot
- Open Graph tags (og:title, og:description, og:image)
- Twitter card tags
- Copyright year in footer (fail if not current year)
- Duplicate link tags in sidebar (known theme bug)
- hreflang configured for French post
- Page speed: count total external scripts loaded
- Check if Cloudflare or CDN is active (look for CF-Ray header or similar)

Output: seo-output/technical-checklist.md

Format:
```
# Technical SEO Checklist

| Check | Status | Fix required |
|-------|--------|-------------|
| HTTPS | PASS | — |
| Viewport meta | PASS | — |
...

## Failed checks — fix instructions
### [Check name]
**Issue:** [description]
**Fix:** [exact steps]
**Priority:** Critical / High / Medium
```

---

### TASK 9 — E-E-A-T assessment

Fetch and analyze:
- https://hybridautopart.com/author/vik/
- https://hybridautopart.com (About Us section in sidebar)
- Any "About" page if it exists

Score each E-E-A-T dimension 1-10:

**Experience (1-10):** Does content show first-hand experience owning/driving hybrid cars?
**Expertise (1-10):** Is Vik's engineering background clearly communicated?
**Authoritativeness (1-10):** Are there bylines, author pages, external mentions?
**Trustworthiness (1-10):** Contact info, privacy policy, accurate facts, fresh dates?

For each dimension, provide:
- Current score and why
- Specific actions to improve score
- Example text to add/change

Output: seo-output/eeat-assessment.md

---

### TASK 10 — Affiliate opportunity audit

For each crawled page, identify:
- Topics covered that have natural product affiliations
- Specific products to recommend (Amazon ASIN if possible)
- Where in the content to naturally place the link
- Estimated commission per sale

Focus on:
- OBD2 scanners (Autel, Launch, BlueDriver)
- Hybrid battery testers
- Prius accessories
- EV chargers / EVSE equipment
- Hybrid car care products
- Engineering/technical books

Output: seo-output/affiliate-opportunities.md

Format:
```
### /blog-en/[slug]/

| Product | Amazon search term | Est. price | Commission | Where to place |
|---------|-------------------|------------|------------|----------------|
...

**Natural placement suggestion:**
"In the section on [X], after mentioning [Y], add: 'To diagnose this yourself, 
the [product name] (link) works well on all Toyota hybrids and shows hybrid-specific codes'"
```

---

### TASK 11 — Prioritized action list

Synthesize ALL findings into a single master action list.

Score each action:
- Impact: 1-5 (5 = highest traffic/revenue impact)
- Effort: 1-5 (1 = 30 min, 5 = full day+)
- Score: Impact / Effort (sort descending — highest score = do first)

Output: seo-output/ACTION_LIST.md

Format:
```
# Master Action List — hybridautopart.com
Generated: [date]
Total actions: [X]

## DO TODAY (Score 4.0+, under 30 min each)
### [score] [action name]
**Page:** [url]
**Impact:** [description of expected result]
**Effort:** [X minutes]
**Exact steps:**
1. [step]
2. [step]

## THIS WEEK (Score 3.0-3.9)
...

## THIS MONTH (Score 2.0-2.9)
...

## CONTENT QUEUE (new posts to write, ranked by traffic potential)
1. [post title] — [est. monthly traffic] — [affiliate opportunity]
...

---
## Summary stats
- Total monthly clicks being lost (fixable with titles): [X]
- Total monthly clicks being lost (fixable with content): [X]  
- Estimated monthly clicks at 3 months after all fixes: [X]
- Estimated monthly clicks at 6 months: [X]
- Estimated monthly revenue at 6 months: $[X]
```

---

### TASK 12 — Executive summary report

Output: seo-output/SUMMARY_REPORT.md

```
# hybridautopart.com — SEO Pipeline Report
Generated: [date]
Pipeline duration: [X minutes]

## Site Health Score: [X]/100

## The 3 most important things to do tomorrow morning:
1. [action] — expected result: [X clicks/mo]
2. [action] — expected result: [X clicks/mo]  
3. [action] — expected result: [X clicks/mo]

## Traffic recovery forecast:
- After title fixes (1 week): [X] visits/mo
- After content fixes (1 month): [X] visits/mo
- After new content (3 months): [X] visits/mo

## Pages crawled successfully: [X/12]
## Pages that blocked crawl: [list]
## Total issues found: [X]
## Critical issues: [X]
## Content gaps identified: [X]
## New post opportunities: [X]

## Files generated:
[list all files in seo-output/ with one-line description each]
```

---

## COMPLETION

When all 12 tasks are done:
1. Print to terminal: "Pipeline complete. Check seo-output/SUMMARY_REPORT.md"
2. Run: `ls -la seo-output/` to show all generated files
3. Run: `wc -l seo-output/*.md` to show file sizes
4. Log "[timestamp] Pipeline complete. [X] files generated." to pipeline.log

Do not stop between tasks.
Do not ask for confirmation.
If a URL is blocked, log it and move on.
This is a background job — be thorough, not fast.
