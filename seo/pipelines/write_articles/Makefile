PIPELINE_NAME := write_articles

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= python3
ENV_FILE   ?= blogs.env
INPUT      ?= input/topics.json
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

export INPUT_JSON := $(INPUT)

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

clean-output: clean

clean-state:
	rm -rf $(OUTPUT_DIR)/run_state
	@echo "Cleared run state"

help:
	@echo "write_articles"
	@echo "  run          — generate articles via AI API (API_KEY required)"
	@echo "  clean        — remove output/"
	@echo "  clean-state  — reset run state (re-run all on next run)"

.PHONY: help run clean-output clean-state

else
include ../../Makefile.pipeline
endif
