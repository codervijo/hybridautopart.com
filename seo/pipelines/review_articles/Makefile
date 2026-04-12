PIPELINE_NAME := review_articles

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= python3
ENV_FILE   ?= review.env
INPUT_DIR  ?= input
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

export INPUT_DIR := $(INPUT_DIR)

.DEFAULT_GOAL := help

run:
	@if [ -z "$(API_KEY)" ] || [ "$(API_KEY)" = "your_key_here" ]; then \
		echo "ERROR: API_KEY is not set in $(ENV_FILE)"; exit 1; \
	fi
	$(PYTHON) main.py

clean-state:
	rm -rf $(OUTPUT_DIR)/run_state
	@echo "Cleared run state"

help:
	@echo "review_articles"
	@echo "  run          — review articles via AI API (API_KEY required)"
	@echo "  clean        — remove output/"
	@echo "  clean-state  — reset run state (re-review all on next run)"

.PHONY: help run clean-state

else
include ../../Makefile.pipeline
endif
