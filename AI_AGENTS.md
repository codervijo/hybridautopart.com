# AI_AGENTS.md — hybridautopart.com & Domain Portfolio

## Overview
This file defines the AI agent roles, responsibilities, and workflows for managing and growing the hybridautopart.com site and the broader domain portfolio owned by Vik Thomas (Lamill Web Systems / lamill.io).

---

## Working memory — Claude instructions

- **After any strategy, insight, or decision is accepted by the user**, update `seo/CLAUDE.md` to reflect it. This keeps future sessions context-complete without relying on conversation history.
- `seo/CLAUDE.md` is the living strategy document for hybridautopart.com SEO. Treat it as the source of truth for content model, author strategy, post roadmap, and technical fixes.
- If a decision contradicts something already in `seo/CLAUDE.md`, update the file — don't leave stale information in place.

---

## Owner profile
- **Name:** Vik Thomas
- **Background:** Experienced embedded systems / motor control engineer
- **Web skills:** WordPress (learning), React/Vite (capable), HTML/CSS (basic)
- **Goal:** Replace main income via web properties within 2–3 years
- **Time available:** ~4 hours/week consistently
- **Primary server:** GoDaddy Managed WordPress (hybridautopart.com)
- **Dev workflow:** Local dev → build → SFTP/SSH deploy

---

## Agent roles

### Agent 1 — SEO & Content Strategist
**Responsibility:** Traffic growth for hybridautopart.com

**Inputs:**
- Google Search Console exports (queries, pages, CTR, position)
- Current post list from WordPress
- Jetpack/GA traffic data

**Tasks:**
- Identify queries with high impressions, low CTR (quick wins)
- Generate optimized title tags and meta descriptions
- Identify content gaps from Search Console query data
- Suggest new posts targeting position 8–20 queries
- Audit existing posts for HCU compliance (thin content, keyword stuffing)
- Monitor traffic trends and flag drops/gains

**Key context:**
- Site peaked at ~45,000 visits/year in 2022
- Hit by Google Helpful Content Update (Aug 2022, Sept 2023)
- Current: ~10,000 visits/year, 399K impressions, 0.5% CTR
- Niche: Toyota Prius / hybrid vehicles — owner has genuine engineering expertise
- Top pages: toyota-prius-power-split-device (57K impr), prius-pwr-mode (69K impr), prius-0-60 (48K impr)
- All posts currently in one "Blog" category — needs topical cluster restructuring

**Prompt to use:**
```
You are an SEO strategist for hybridautopart.com, a Toyota Prius and hybrid vehicle blog.
The site was hit by Google's Helpful Content Update and traffic dropped 75% from 2022 peak.
Owner is an embedded systems engineer with genuine expertise in hybrid drivetrains.
Current stats: 10K visits/year, 399K impressions, 0.5% CTR, avg position 18.7.
[Attach Search Console export CSV]
Task: [your specific task]
```

---

### Agent 2 — React/Vite Developer
**Responsibility:** Build and maintain interactive tools for hybridautopart.com

**Primary project:** Toyota Power Split Device Simulator
- WordPress plugin: `wp-content/plugins/psd-simulator/`
- React app source: `psd-simulator/react-app/`
- Shortcode: `[psd_simulator]`
- Target page: `/blog-en/toyota-prius-power-split-device/`

**Build workflow:**
```bash
cd psd-simulator/react-app
npm install
npm run dev        # dev server localhost:5173
npm run build      # outputs to ../plugin/dist/
```

**Deploy workflow:**
```bash
scp -r plugin/ user@server:/var/www/html/wp-content/plugins/psd-simulator/
```

**Technical constraints:**
- Must mount to `#psd-root` (not `#root`)
- Bundle size target: <150KB gzipped
- No external API calls — all logic client-side
- Must work on mobile (touch sliders)
- WordPress PHP plugin auto-detects shortcode pages and enqueues JS/CSS only there

**Prompt to use:**
```
You are a React/Vite developer working on the Toyota PSD Simulator WordPress plugin.
Project is in psd-simulator/ with react-app/ source and plugin/ for WordPress deployment.
The simulator mounts to #psd-root via WordPress shortcode [psd_simulator].
Owner is an embedded engineer who understands the planetary gear math.
Current state: basic prototype with speed/throttle sliders and canvas animation.
Task: [your specific task]
See HANDOFF_PROMPT.md for full technical context.
```

---

### Agent 3 — WordPress Manager
**Responsibility:** WordPress site health, plugins, themes, and configuration

**Site details:**
- URL: hybridautopart.com
- Host: GoDaddy Managed WordPress
- SEO plugin: Yoast SEO (free)
- Stats: Jetpack
- Theme: custom (has duplicate link tag bug in Recent Content widget)

**Known issues to fix:**
1. Footer shows © 2022 — update to dynamic year
2. "Recent Content" widget outputs duplicate `link to [Title]` anchor tags — theme bug
3. About Us sidebar says "Lamill Web Systems creates content" — hurts E-E-A-T
4. All posts in single "Blog" category — needs topical clusters
5. No breadcrumbs enabled (Yoast has this built in — just needs enabling)
6. No FAQ schema on posts that have FAQ sections
7. No Article schema on blog posts
8. No "Last Updated" dates visible on posts

**Prompt to use:**
```
You are a WordPress developer managing hybridautopart.com on GoDaddy Managed WordPress.
Yoast SEO (free) is installed. Theme has a known duplicate link tag bug in sidebar.
Task: [your specific task]
```

---

### Agent 4 — Domain Portfolio Manager
**Responsibility:** Track, optimize, and monetize domain portfolio

**Portfolio summary (as of April 2026):**

| Domain | Status | Action | Notes |
|--------|--------|--------|-------|
| lamill.io | Keep | Core brand | |
| lamill.us | Keep | Core brand | |
| lamillrentals.com | Keep | Core brand | |
| kwizicle.com | Keep | Infographics idea | |
| plaira.io | Keep | Has WP blog | |
| dunam.co | Keep | Short .co premium | |
| airsucks.com | Keep | Suction/vacuum niche | |
| whizgraphs.com | Keep | Infographics brand | |
| hybridautopart.com | Build | PRIMARY ASSET | 1K visits/mo, unmonetized |
| iotbastion.com | Build | IoT security blog | Owner's engineering expertise |
| streamsgalaxy.com | Build | Streaming guides | Has existing traffic |
| airgiveaway.com | Build | Giveaway/sweepstakes | TBD |
| smartlyworld.com | Sell | List on Afternic | $300–800 |
| carrepairsite.com | Sell | Build then sell | Auto repair directory |
| itunesucks.com | Sell | List on Afternic | $500–1500 novelty |
| iotnews.today | Sell | Build then sell | IoT news aggregator |
| swiftly.co.in | Sell | List on Afternic | $100–300 |
| maslist.com | Sell | List on Afternic | $300–800 |
| virtually.co.in | Sell | List on Afternic | $100–300 |
| veezp.com | Sell | List on Afternic | $100–200 |
| navodayansonline.com | Alumni | Simple WP site | |
| vijocherian.com | Alumni | Personal name | |
| thakinaam.com | Alumni | Alumni group | |
| nosapta.com | Alumni | Alumni group | |
| yesuinnu.com | Alumni | Alumni group | |
| thakiweb.com | Alumni | Alumni group | |
| cricketfansite.com | Alumni | Cricket community | |

**Cancelled (as of April 2026):**
airplanesandcars.com, winmacbookair.com, macbookairfree.com, macbookairgames.com,
macbookairmusic.com, fixmacbookair.com, iotw00t.com, newiniot.com, thakilists.com,
winmacbook.com, picsonaphone.com, picsonphones.com, cameraphoneadvisor.com,
appsupermaket.com, picsonmyphone.com, applicationsuperstore.com

**Still to cancel:**
airgiveaway.com ← KEEP (repurposed)
iotbastion.com ← KEEP (repurposed)

**Annual cost after cleanup:** ~$270–$300/year (domains only, excluding hosting)

**Prompt to use:**
```
You are managing a domain portfolio for Vik Thomas (Lamill Web Systems).
See AI_AGENTS.md for full portfolio status and strategy.
Task: [your specific task]
```

---

### Agent 5 — Monetization Strategist
**Responsibility:** Revenue strategy across all web properties

**Income targets:**
- Month 6: $200–500/mo (affiliate links on hybridautopart.com)
- Month 12: $500–1,000/mo (ads + affiliate on hybridautopart + iotbastion)
- Month 18: $1,000–2,000/mo (add domain sales + streamsgalaxy)
- Month 36: $3,000–5,000/mo (replace main income)

**Monetization by site:**
- hybridautopart.com: Amazon Associates (auto parts, OBD scanners) + Mediavine ads (at 10K sessions)
- iotbastion.com: Affiliate (security tools, dev boards, books) + newsletter
- streamsgalaxy.com: Ezoic/Mediavine ads + streaming service affiliate
- carrepairsite.com: Lead generation for local mechanics ($20–50/lead)
- Domain sales: Afternic passive listings for sell-category domains

**Prompt to use:**
```
You are a monetization strategist for a portfolio of web properties owned by Vik Thomas.
Primary site: hybridautopart.com (hybrid car blog, 10K visits/year, unmonetized).
Owner is an embedded systems engineer targeting $3–5K/mo within 3 years.
Task: [your specific task]
```

---

## Weekly workflow (4 hrs/week)

| Day | Task | Agent | Time |
|-----|------|-------|------|
| Monday | Check Search Console — note trending queries | Agent 1 | 30 min |
| Tuesday | Write/edit one post for hybridautopart.com | Agent 1 | 90 min |
| Wednesday | Publish + promote (Reddit, LinkedIn, Twitter) | Agent 1 | 30 min |
| Thursday | PSD simulator development | Agent 2 | 60 min |
| Weekend | Domain/WordPress maintenance or monetization task | Agents 3/4/5 | 30 min |

---

## Key resources
- Search Console: https://search.google.com/search-console (property: hybridautopart.com)
- GoDaddy: https://account.godaddy.com/products
- Afternic (domain sales): https://www.afternic.com
- Amazon Associates: https://affiliate-program.amazon.com
- Mediavine (ads, requires 10K sessions/mo): https://www.mediavine.com
- PriusChat forums (community outreach): https://priuschat.com
- r/prius (180K members): https://reddit.com/r/prius
- r/iotsecurity: https://reddit.com/r/iotsecurity

---

## Git repo recommendation
Create a monorepo to track everything:
```
lamill-web/
├── hybridautopart/
│   └── plugins/
│       └── psd-simulator/     ← current plugin
├── iotbastion/
├── streamsgalaxy/
├── domains/
│   └── portfolio.csv          ← domain tracker
└── AI_AGENTS.md               ← this file
```
