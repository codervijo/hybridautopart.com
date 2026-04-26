PIPELINE_NAME := analyze_audit_results

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= uv run python3
ENV_FILE   ?= analyze.env
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

help:
	@echo "analyze_audit_results"
	@echo "  run    — read latest audit data, write data/reports/YYYY-MM-DD/"
	@echo "           (summary.md, todo.md, diff.md, details/*.md)"

.PHONY: help run

else
include ../../Makefile.pipeline
endif
