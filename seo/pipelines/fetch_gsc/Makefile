PIPELINE_NAME := fetch_gsc

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= uv run python3
ENV_FILE   ?= gsc.env
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

help:
	@echo "fetch_gsc"
	@echo "  run    — read CSVs from data/gsc/inbox/, write data/gsc/{date}.json"
	@echo ""
	@echo "Drop GSC CSV exports into data/gsc/inbox/ before running:"
	@echo "  - Queries  (Performance → Export)"
	@echo "  - Pages    (Performance → Export)"
	@echo "  - Coverage (Pages → click status → Export, e.g. crawled-not-indexed.csv)"

.PHONY: help run

else
include ../../Makefile.pipeline
endif
