# Playbook: canonical_cross_language

> Seed playbook captured 2026-04-26 from a real fix session on hybridautopart.com.
> AI-driven `guided_fix` will load this on next encounter and use it as primary guidance,
> deviating only if the WP UI or symptom doesn't match.

## Symptom

`<link rel="canonical" href="https://hybridautopart.com/fr/<slug>/" />` appears in the live HTML
of an English page (the source URL has no `/fr/` prefix). OpenGraph `og:url` and JSON-LD
`@id` typically also point to the wrong-language path.

## Cause

Yoast's indexable table (`wp_yoast_indexable`) caches per-post permalinks for performance.
When Polylang was active, those rows were populated with `/fr/...` permalinks. Removing
the Polylang plugin doesn't touch that table — Yoast keeps reading from it.

The postmeta `_yoast_wpseo_canonical` field on the affected pages is **empty** in the WP
Yoast UI, which can mislead. The override is in the indexable table, not in postmeta.

## Steps (per affected URL)

1. WP Admin → **Pages** (or **Posts** if not in Pages)
2. Find the page by title or slug. Click **Edit**.
3. **Click Save** (top right). No content changes needed — `save_post` triggers Yoast to
   rebuild the indexable for that single post using the current permalink.
4. **Verify**: open the public URL with a cache-bust query (e.g. `?bustcache=1`), View Source,
   search for `canonical`. Should now self-reference, not point to `/fr/...`.

## Verification command

```bash
curl -s "https://hybridautopart.com/<path>/?bustcache=1" \
  | grep -iE 'rel=["'\'']?canonical["'\'']?'
```

Expected:
```
<link rel="canonical" href="https://hybridautopart.com/<path>/" />
```

## Pitfalls

- **"Field is empty in WP UI" ≠ "live HTML is correct".** Yoast UI shows postmeta; the
  bug lives in the indexable table.
- **Page cache.** GoDaddy Managed WordPress serves cached HTML. Always cache-bust before
  declaring success — `?bustcache=1` is enough.
- **Yoast → Tools → SEO data optimization** rebuilds indexables but can miss individual
  records. Run it as a precondition, but the per-page Save trick is the reliable fix.
- **Don't try to clear `_yoast_wpseo_canonical` postmeta** — it's already empty. The fix is
  to *trigger an indexable rebuild*, not edit postmeta.

## Bulk variant

If many pages are affected (we had 7), the per-page Save loop is ~30 seconds each. Total ~5
minutes for a typical batch. There is no UI for "rebuild indexables for these N pages
specifically".

When WP REST API integration ships (V2 P1), this becomes scriptable: POST to each page's
endpoint with empty body to trigger `save_post`.

## Cleanup follow-ups

After the canonical fix, also consider:

- **Trash leftover translated posts** at `/fr/<slug>/`, `/blog/<french-slug>/`, etc. They're
  thin content pulling traffic away from the English versions and may still be in your sitemap.
- **Drop Polylang DB tables** if you're confident no other i18n plugin will use them: `wp_pll_*`.
  These survive Polylang's `uninstall.php` by design.
