PIPELINE_NAME := guided_fix

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= uv run python3
ENV_FILE   ?= guided.env
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

help:
	@echo "guided_fix"
	@echo "  run             — interactive walk through pending audit todo items"
	@echo "  ITEM=<slug> run — walk only the matching item (e.g. ITEM=canonical_cross_language)"
	@echo ""
	@echo "Requires ANTHROPIC_API_KEY in seo.env. Reads latest audit data from data/."
	@echo "Resumes from data/reports/<today>/work-log.md."

.PHONY: help run

else
include ../../Makefile.pipeline
endif
