ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)
  PYTHON ?= python3
  .DEFAULT_GOAL := help
  include Makefile.local
else
  SEO_DIR := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST))))../..)
  .DEFAULT_GOAL := help
  help:
	@echo "write_articles  (run outside Docker)"
	@echo "  make buildsh     — enter the Docker dev container"
	@echo ""
	@echo "Inside the container, available targets:"
	@echo "  run              — generate articles (template mode, no API)"
	@echo "  run-ai           — generate articles via AI API"
	@echo "  clean            — remove output/"
	@echo "  clean-state      — reset run state (re-run all on next run)"
  buildsh:
	$(MAKE) -C $(SEO_DIR) buildsh
  %:
	@echo "Not in Docker. Run 'make buildsh' from $(SEO_DIR) to enter the container, then: make $@"
	@false
  .PHONY: help buildsh
endif
