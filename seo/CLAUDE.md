# CLAUDE.md — hybridautopart.com SEO Strategy

See also: `../AI_AGENTS.md` for full site context, agent roles, and domain portfolio.

---

## SEO Pipeline — Status

Pipeline completed 2026-04-16. All output in `seo-output/`.

| File | What's in it |
|------|-------------|
| `SUMMARY_REPORT.md` | Executive summary, scores, forecasts |
| `ACTION_LIST.md` | 42 actions ranked by Impact/Effort |
| `content-briefs.md` | 10 new post outlines with opening drafts |
| `meta-descriptions.md` | Ready-to-paste meta descs for all 12 pages |
| `faq-schema.md` | JSON-LD FAQ schema for 7 pages |
| `internal-links.md` | 16 broken links + 18 new link opportunities |
| `eeat-assessment.md` | E-E-A-T scored 22/40 with fix plan |
| `technical-checklist.md` | PASS/FAIL checklist + fix instructions |
| `affiliate-opportunities.md` | Product placements per page |
| `ctr-analysis.md` | 575 clicks/month being left on table |
| `content-audit.md` | Full HCU + technical audit per page |
| `crawl/*.json` | Per-page structured data (12 files) |

**Site health score: 34/100**

---

## Critical Fixes (do first, <1 hour total)

1. **Remove Lamill Web Systems attribution from About Us sidebar**
   - WordPress Admin → Appearance → Widgets → About Us widget
   - Replace with: "HybridAutoPart.com explains hybrid technology from an embedded systems and motor control engineering perspective. No ads fluff, no dealer bias."
   - This appears sitewide and is the #1 E-E-A-T issue on the site

2. **Add meta descriptions to prius-0-60 and prius-pwr-mode**
   - 48K and 70K impressions/year at <0.3% CTR — Google is writing its own poor snippets
   - Use exact text from `seo-output/meta-descriptions.md`

3. **Fix /blog/ → /blog-en/ broken internal links**
   - One `.htaccess` line: `Redirect 301 /blog/ /blog-en/`
   - Fixes 16 broken links across 7 pages at once

4. **Fix Subaru Crosstrek factual error on PSD page**
   - Crosstrek is listed as using Toyota's Power Split Device — it does not
   - Remove it from the PSD vehicle list, add a clarifying note

---

## Author / Persona Strategy

**"Vik Thomas" is a pen name. The real author's identity is not to be revealed.**

This is normal and fine. Don't build fake off-site signals (LinkedIn profile, forum history, third-party citations for the persona) — these create fragility and Google is getting better at detecting fabricated entity corroboration.

**The strategy: content corroboration, not author corroboration.**

Google can't verify who Vik is. But it can verify that the content is technically accurate, specific, and consistent. That's what matters.

### What to fix (honest, no fabrication)

**Author page** (`/author/vik/` — currently empty):
> "The articles on this site are written from an embedded systems and motor control engineering background. I own a Toyota Prius and have been writing about hybrid technology since [year]."

No real name, no photo, no LinkedIn required.

**About Us sidebar** (replace Lamill text with):
> "HybridAutoPart.com explains hybrid technology from an engineering perspective. No ads fluff, no dealer bias."

**Bylines:** Optional. Can drop "By Vik Thomas" entirely and publish without a byline if the persona feels uncomfortable to maintain. The brand can be the authority instead of a named person.

### Realistic E-E-A-T ceiling for a persona site

| Signal | Real author | Persona |
|---|---|---|
| On-site bio/credentials | Strong | Moderate |
| Off-site corroboration | Achievable | Not realistic |
| Content quality signals | Same | Same |
| Long-term E-E-A-T ceiling | High | Medium |

Traffic forecast realistically tops out at ~60–70% of the modeled numbers without off-site author corroboration. Still meaningful — 4,000–7,000 visits/month at 10 posts.

---

## Content Model

**Do not outsource writing entirely to AI or generic freelancers.** The engineering depth in existing content is the real differentiator. Generic hybrid content is abundant — Google is deprioritising it.

**The split that works:**

| Part | Who does it | Time |
|---|---|---|
| Outline, headings, FAQ, schema, internal links, meta desc | Claude | — |
| Technical sections (how the system works) | Claude (from existing site corpus) | — |
| Intro paragraph (first-person, engineering angle) | Owner | ~20 min/post |
| Any "I've seen this on my own Prius..." sections | Owner | ~10 min/post |
| Review and publish | Owner | ~10 min/post |

Total owner time per post: ~30–45 minutes. Gets to 90%+ of traffic forecast vs 20–40% for pure AI content.

---

## Post Forecast (by number of posts published)

Baseline assumes quick fixes done. Assumes 1–2% CTR as posts establish rankings.

| Posts | Titles added | Est. visits/mo |
|---|---|---|
| 0 (quick fixes only) | — | 1,500–2,000 |
| +1 | How Long Do Hybrid Batteries Last (8K searches/mo) | 2,000–2,500 |
| +2 | + Toyota Hybrid Battery Replacement Cost (6K) | 2,500–3,200 |
| +3 | + FHEV Meaning (4K) | 2,800–3,500 |
| +4 | + Prius Prime Real-World EV Range (3.5K) | 3,200–4,200 |
| +5 | + RAV4 Hybrid PWR Mode (3K) | 3,500–4,800 |
| +6 | + Toyota Prius Models by Year (2.5K) | 3,800–5,200 |
| +7 | + Hybrid Battery Degradation (2K) | 4,000–5,600 |
| +8 | + Best OBD2 Scanner for Prius (1.8K, HIGH affiliate) | 4,200–6,000 |
| +9 | + Prius Transmission Problems (1.8K) | 4,400–6,400 |
| +10 | + Toyota vs Honda Hybrid Reliability (1.5K) | 4,600–7,000 |

Posts 1–2 (battery life + cost) are the highest-leverage pair — they share internal links and compound each other's authority. Posts 8–10 have the highest affiliate conversion potential.

---

## Revenue Projection

| Visits/mo | Est. affiliate revenue/mo |
|---|---|
| 1,500–2,000 | $100–200 |
| 3,500–4,800 | $300–600 |
| 6,000–7,000 | $600–1,000 |

Mediavine ad eligibility kicks in at 10K sessions/month — a parallel goal to the post publishing schedule.

---

## Key Insight from SEO Audit

The content quality is genuinely strong — the Power Split Device explanation, HSD mechanics, and technical accuracy exceed most competitors. **The problem is not the content. It is the trust and engagement signals surrounding it.**

- 399K impressions/year at 0.5% CTR = traffic is there, not converting
- The Lamill attribution is the most self-inflicted SEO wound on the site
- Engineering expertise is completely invisible to Google and readers
- Every page is missing metadata Google uses to assess engagement

Fastest path to recovery: credibility restoration (E-E-A-T fixes) + engagement optimization (meta descs + title rewrites). New content is the growth layer on top.
