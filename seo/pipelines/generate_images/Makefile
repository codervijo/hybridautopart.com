PIPELINE_NAME := generate_images

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)

PYTHON     ?= python3
ENV_FILE   ?= images.env
INPUT_DIR  ?= input
OUTPUT_DIR ?= output/posts
include ../../Makefile.pipeline-common

export INPUT_DIR := $(INPUT_DIR)

.DEFAULT_GOAL := help

run:
	USE_IMAGE_AI=false $(PYTHON) main.py

run-ai:
	@if [ -z "$(IMAGE_API_KEY)" ] || [ "$(IMAGE_API_KEY)" = "your_key_here" ]; then \
		echo "ERROR: IMAGE_API_KEY is not set in $(ENV_FILE)"; exit 1; \
	fi
	USE_IMAGE_AI=true $(PYTHON) main.py

clean-manifests:
	find $(OUTPUT_DIR) -name manifest.json -delete
	@echo "Cleared all manifests (images preserved)"

clean-images:
	find $(OUTPUT_DIR) -path "*/images/*.webp" -delete
	find $(OUTPUT_DIR) -name manifest.json -delete
	@echo "Cleared images and manifests"

help:
	@echo "generate_images"
	@echo "  run              — generate placeholder SVG images"
	@echo "  run-ai           — generate real images via AI API (IMAGE_API_KEY required)"
	@echo "  clean            — remove output/"
	@echo "  clean-manifests  — reset manifests only (keeps images)"
	@echo "  clean-images     — remove images and manifests"

.PHONY: help run run-ai clean-manifests clean-images

else
include ../../Makefile.pipeline
endif
