# Playbook: multiple_h1

> Pre-seed playbook (no live session yet for this type).

## Symptom

The page emits more than one `<h1>` tag. The crawl's `h1` field shows multiple entries,
e.g. `["Privacy Policy", "Last updated"]`.

## Cause

WordPress block editor allows any block to be set to "Heading 1". Themes sometimes also
emit an H1 in the page header (logo or page-title block) **plus** a second H1 inside the
post content. This is theme-specific and content-specific.

## Steps

1. Look at the H1 list in the audit data (already in context — don't ask the user to
   paste it). The first one is usually the legitimate page heading; subsequent ones are
   the bug.
2. Tell the user the page-edit URL: `https://<site>/wp-admin/edit.php?post_type=page` —
   then have them search by title and click Edit.
3. In the block editor, ask the user to **click the heading text** that matches the second
   H1 string (e.g. "Last updated"). The block toolbar appears.
4. In the block toolbar, click the heading-level dropdown (looks like `H1` or three lines).
   Change it from **H1** to **H2** (or H3, whichever fits the visual hierarchy).
5. Click **Update** (top right).
6. Verify: open `https://<site>/<path>/?bustcache=1`, View Source, search `<h1`. Expect
   exactly one match.

## Verification command

```bash
curl -s "https://<site>/<path>/?bustcache=1" | grep -c '<h1'
```

Expected output: `1`.

## Pitfalls

- The "site title" or "logo" sometimes wraps in an `<h1>` via the theme. If verification
  shows >1 H1 and only one of them is editable in the post body, the extra H1 is in the
  theme's `header.php`. Surface this to the user — they can either (a) edit the theme
  template (advanced; risk of being overwritten on theme update), or (b) accept it and
  move on (the duplicate-H1 SEO penalty is minor compared to the cost of editing themes).
- "Heading 1" in the block editor's drop-down looks like a regular formatting choice. The
  user may not realize the block-level heading IS an `<h1>` until you point it out.
- GoDaddy page cache may serve stale HTML — `?bustcache=1` is required for verification.

## Notes

- This is a low-impact issue (Impact 3 in the audit). If the source of the second H1 is a
  theme template and editing the theme is risky, advise the user to skip and move on.
