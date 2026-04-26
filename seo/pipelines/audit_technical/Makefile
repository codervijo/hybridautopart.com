PIPELINE_NAME := audit_technical

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= uv run python3
ENV_FILE   ?= audit.env
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

help:
	@echo "audit_technical"
	@echo "  run    — read latest crawl, emit data/audits/technical/YYYY-MM-DD.json"
	@echo "  clean  — remove output/ (this stage has no output dir of its own)"

.PHONY: help run

else
include ../../Makefile.pipeline
endif
