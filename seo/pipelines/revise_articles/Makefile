PIPELINE_NAME := revise_articles

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON              ?= python3
ENV_FILE            ?= revise.env
INPUT_ARTICLES_DIR  ?= input/articles
INPUT_REVIEWS_DIR   ?= input/reviews
OUTPUT_DIR          ?= output
include ../../Makefile.pipeline-common

export INPUT_ARTICLES_DIR := $(INPUT_ARTICLES_DIR)
export INPUT_REVIEWS_DIR  := $(INPUT_REVIEWS_DIR)

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
	@echo "revise_articles"
	@echo "  run          — apply review improvements via AI API (API_KEY required)"
	@echo "  clean        — remove output/"
	@echo "  clean-state  — reset run state (re-revise all on next run)"

.PHONY: help run clean-state

else
include ../../Makefile.pipeline
endif
