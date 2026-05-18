# CLAUDE.md — hybridautopart.com (project-level)

For SEO pipeline specifics, see `seo/CLAUDE.md`.
For site-wide AI agent context, see `AI_AGENTS.md`.

## Deferred follow-ups

Items raised during a session but pushed to a future pass — kept here so they
don't disappear into chat history.

### Content edits (separate from CTR title/meta walk)

- **`/blog-en/prius-pwr-mode/` — add H2 "How to turn PWR mode off"**
  Surfaced 2026-05-10 during low-CTR walk. Google's PAA box for "prius pwr mode"
  shows "How to turn off pwr mode on Prius?" as a top user question, but the
  page doesn't address it. Add a short section with the actual procedure
  (press the PWR button again to deselect; mode reverts to Normal). Do this
  *after* the title/meta walk so CTR effects can be measured separately from
  on-page changes.

### Pipeline / tooling

- **Add `find_post_id` tool to `seo/pipelines/guided_fix/main.py`** — wrap the
  WP REST slug→ID lookup so the AI can print real edit URLs (no manual search
  in WP admin). Endpoint: `GET /wp-json/wp/v2/posts?slug=<slug>&_fields=id`.

- **Restructure `guided_fix` system prompt to require the structured card
  output format** (see the cards used in the 2026-05-10 manual walk for shape).
  Current prompt yields prose; cards are scannable and consistent.

- **Consider per-issue-type model selection in `guided_fix`.** GPT-4.1-mini is
  fine for technical fixes; CTR rewrites benefit from a stronger model. One
  config knob: model override per playbook.

## Project

<1-2 sentence description — fill in what hybridautopart.com does and who the
user is. The stack uses the sites/* workspace shared infra: Vite or
Astro + pnpm + Cloudflare Pages, with Makefile forwarding to the
central builder at `~/work/projects/builder/`.>

## Commands

```bash
# Build / dev (forwards to the parent Makefile)
make deps           # install deps via the central builder
make dev            # local dev server
make build          # production build → dist/

# Deploy
git push            # Cloudflare Pages auto-builds on push to main
```


## Heading hygiene

**Before adding any section, subsection, or heading to a Markdown
file, output the file's current heading outline first:**

```bash
grep -nE '^#+ ' path/to/file.md
```

Then confirm — in the chat — that the planned new heading's:

1. **Depth** (`#`, `##`, `###`, …) is the intended depth, not
   accidentally one level too shallow.
2. **Label** doesn't collide with existing headings — no duplicate
   `## 1. <title>`, no `### N.X` subsection labels that look like
   `vN.X` phase identifiers.

Only after that confirmation, write.

Applies especially to long-lived docs: `docs/prd.md`, `AI_AGENTS.md`,
`docs/architecture.md`, `docs/CLAUDE.md`.

**Why:** structural drift is invisible in any single editing session
— it only becomes obvious in the aggregate, by which time the doc is
hard to fix. The pre-edit outline ritual catches collisions and depth
mistakes at the point of writing, not at quarterly cleanup time.

