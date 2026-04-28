ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)
  BUILDER_PATH ?= /usr/builder
else
  BUILDER_PATH ?= $(HOME)/work/projects/builder
endif
include $(BUILDER_PATH)/Makefile

PROJECT_NAME := seo-blog-generator
PYTHON       := python3

# `deps` and `test` are provided by builder's Makefile.python (uv-based).
# pytest.ini's `testpaths = tests` handles the test path.

# ─── Audit chain ─────────────────────────────────────────────────────────────
# `audit-all` is an ordering preference, not a hard dependency. Each stage's
# failure does NOT abort the chain — analyze_audit_results runs unconditionally
# at the end and reports on whatever data exists. Stages not yet built are
# skipped with a notice.

.PHONY: analyze audit-all guided

analyze:
	$(MAKE) -C pipelines/analyze_audit_results run

# Interactive AI-driven walkthrough of audit todo items.
# Pass ITEM=<slug> to limit to one issue type, e.g.:
#   make guided ITEM=canonical_cross_language
guided:
	$(MAKE) -C pipelines/guided_fix run

audit-all:
	-$(MAKE) -C pipelines/crawl_site run
	-$(MAKE) -C pipelines/audit_technical run
	-$(MAKE) -C pipelines/audit_content run
	-$(MAKE) -C pipelines/fetch_gsc run
	@if [ -d pipelines/compare_runs ]; then $(MAKE) -C pipelines/compare_runs run || true; \
	  else echo "compare_runs: not yet built, skipping"; fi
	$(MAKE) -C pipelines/analyze_audit_results run
