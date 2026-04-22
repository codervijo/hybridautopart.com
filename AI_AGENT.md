# AI Agent Context — hybridautopart.com

## What this project is
hybridautopart.com is a Toyota Prius and hybrid vehicle technical blog targeting 10K visits/month in 12 months and 100K/month in 24 months. It uses an AI-assisted content pipeline to produce engineering-depth articles at scale (~3 posts/week) while the owner contributes the hands-on engineering voice.

## Stack
- **Content pipelines:** Python 3, OpenAI-compatible API (currently GPT-4.1-mini), Markdown output
- **WordPress plugins:** React + Vite, compiled to static JS/CSS, deployed via SFTP
- **CMS:** WordPress 6.5 on GoDaddy Managed WordPress, Yoast SEO (free)
- **Deploy:** local build → SFTP/SSH to GoDaddy server

## Project structure
```
hybridautopart.com/
├── seo/                        # All SEO and content pipeline work
│   ├── pipelines/
│   │   ├── generate_article_ideas/   # Keyword expansion → topics.json
│   │   ├── write_articles/           # topics.json → Markdown drafts
│   │   ├── review_articles/          # Draft QA: HCU + structure check
│   │   ├── revise_articles/          # Apply review feedback
│   │   ├── generate_images/          # Article image generation
│   │   └── embed_images/             # Embed images into Markdown
│   ├── plugin-builder/               # Claude → WordPress shortcode plugins
│   ├── lib/                          # Shared Python utilities
│   ├── seo-output/                   # SEO audit results (crawl, CTR, E-E-A-T)
│   ├── topics.json                   # Active content queue
│   └── CLAUDE.md                     # Living SEO strategy (source of truth)
├── docs/                       # PRD, prompts log, strategy docs
├── AI_AGENTS.md                # Detailed agent roles and prompt templates
├── plan.md                     # Content funnel strategy
└── deep-research-report.md     # Niche/competitor research
```

## How to run

```bash
# Generate article ideas from seed keywords
cd seo/pipelines/generate_article_ideas && make run

# Write articles from topics queue
cd seo/pipelines/write_articles && make run

# Review drafted articles
cd seo/pipelines/review_articles && make run

# Build a WordPress plugin from an idea spec
cd seo/plugin-builder && make run

# Run SEO audit (Claude Code agent)
cat seo/SEO_PIPELINE_PROMPT.md | claude --dangerously-skip-permissions --print
```

Each pipeline reads config from its own `.env` file. Copy `blogs.env.orig` → `blogs.env` and set `API_KEY`.

## Key conventions
- Each pipeline has its own `blogs.env` / `ideas.env` / etc. — never share secrets across pipelines
- Articles are generated as Markdown in `output/posts/{slug}.md` — owner edits before WordPress publish
- Run state is tracked in `output/run_state/` — delete `run_state/` to re-run all topics
- `seo/CLAUDE.md` is the living strategy doc — update it when strategy decisions are made
- Pen name "Vik Thomas" — do not reveal real author identity, do not fabricate off-site signals

## Out of scope / don't touch
- WordPress database or server config directly (GoDaddy Managed — SSH access is limited)
- Publishing to WordPress without owner engineering review pass
- Creating backlinks artificially or building fake author profiles
