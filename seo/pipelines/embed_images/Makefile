PIPELINE_NAME := embed_images

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= python3
ENV_FILE   ?= embed.env
INPUT_DIR  ?= input
OUTPUT_DIR ?= output/posts
include ../../Makefile.pipeline-common

export INPUT_DIR := $(INPUT_DIR)

.DEFAULT_GOAL := help

run:
	$(PYTHON) main.py

clean-manifests:
	find $(OUTPUT_DIR) -name manifest.json -delete 2>/dev/null || true
	@echo "Cleared all manifests"

help:
	@echo "embed_images"
	@echo "  run              — embed images into article Markdown"
	@echo "  clean            — remove output/"
	@echo "  clean-manifests  — reset manifests (force re-embed on next run)"

.PHONY: help run clean-manifests

else
include ../../Makefile.pipeline
endif
