PIPELINE_NAME := audit_content

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= uv run python3
ENV_FILE   ?= audit.env
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

help:
	@echo "audit_content"
	@echo "  run    — read latest crawl, emit data/audits/content/YYYY-MM-DD.json"
	@echo "           (thin pages + near-duplicate clusters via TF-IDF cosine)"

.PHONY: help run

else
include ../../Makefile.pipeline
endif
