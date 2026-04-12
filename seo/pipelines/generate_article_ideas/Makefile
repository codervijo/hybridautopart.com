ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)
  PYTHON ?= python3
  .DEFAULT_GOAL := help
  include Makefile.local
else
  SEO_DIR := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST))))../..)
  .DEFAULT_GOAL := buildsh
  buildsh:
	$(MAKE) -C $(SEO_DIR) buildsh
  %:
	@echo "Not in Docker. Run 'make buildsh' from $(SEO_DIR) to enter the container, then: make $@"
	@false
  .PHONY: buildsh
endif
