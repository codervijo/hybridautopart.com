PIPELINE_NAME := generate_article_ideas

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= python3
ENV_FILE   ?= ideas.env
INPUT_DIR  ?= input
OUTPUT_DIR ?= output
include ../../Makefile.pipeline-common

export INPUT_DIR := $(INPUT_DIR)

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

run-patterns:
	USE_AUTOCOMPLETE=false $(PYTHON) main.py

run-autocomplete:
	USE_PATTERNS=false $(PYTHON) main.py

run-ai:
	@if [ -z "$(API_KEY)" ] || [ "$(API_KEY)" = "your_key_here" ]; then \
		echo "ERROR: API_KEY is not set in $(ENV_FILE)"; exit 1; \
	fi
	USE_AI=true $(PYTHON) main.py

help:
	@echo "generate_article_ideas"
	@echo "  run              — expand seeds (patterns + autocomplete)"
	@echo "  run-patterns     — pattern expansion only (no network)"
	@echo "  run-autocomplete — autocomplete expansion only"
	@echo "  run-ai           — LLM-generated ideas with cluster/priority/links"
	@echo "  clean            — remove output/"

.PHONY: help run run-patterns run-autocomplete run-ai

else
include ../../Makefile.pipeline
endif
