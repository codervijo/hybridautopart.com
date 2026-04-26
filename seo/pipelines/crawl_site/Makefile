PIPELINE_NAME := crawl_site

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= uv run python3
ENV_FILE   ?= crawl.env
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

clean-state:
	rm -f $(OUTPUT_DIR)/pages.jsonl
	@echo "Cleared crawl state (pages.jsonl)"

help:
	@echo "crawl_site"
	@echo "  run          — fetch sitemap and crawl all URLs (polite, rate-limited)"
	@echo "  clean        — remove output/"
	@echo "  clean-state  — clear pages.jsonl (force full re-crawl on next run)"

.PHONY: help run clean-state

else
include ../../Makefile.pipeline
endif
