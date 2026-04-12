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
	USE_AI=false $(PYTHON) main.py

run-ai:
	@if [ -z "$(API_KEY)" ] || [ "$(API_KEY)" = "your_key_here" ]; then \
		echo "ERROR: API_KEY is not set in $(ENV_FILE)"; exit 1; \
	fi
	USE_AI=true $(PYTHON) main.py

clean-output: clean

clean-state:
	rm -rf $(OUTPUT_DIR)/run_state
	@echo "Cleared run state"

help:
	@echo "write_articles"
	@echo "  run          — generate articles (template mode, no API)"
	@echo "  run-ai       — generate articles via AI API"
	@echo "  clean        — remove output/"
	@echo "  clean-state  — reset run state (re-run all on next run)"

.PHONY: help run run-ai clean-output clean-state

else
include ../../Makefile.pipeline
endif
