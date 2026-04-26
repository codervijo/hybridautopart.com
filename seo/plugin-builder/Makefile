.PHONY: run build-only clean help

# Run full pipeline (LLM + Docker build)
run:
	cd "$(dir $(abspath $(lastword $(MAKEFILE_LIST))))" && \
	python3 build.py

# Run without Docker build step (LLM + write files only)
build-only:
	cd "$(dir $(abspath $(lastword $(MAKEFILE_LIST))))" && \
	DOCKER_BUILD=false python3 build.py

# Run a single idea by slug: make slug=vin-checker one
one:
	cd "$(dir $(abspath $(lastword $(MAKEFILE_LIST))))" && \
	IDEAS_DIR=ideas OUTPUT_DIR=output python3 -c "\
from pathlib import Path; \
import sys; sys.path.insert(0, '..'); \
exec(open('build.py').read()); \
config = get_config(); \
state = __import__('lib.run_state', fromlist=['RunState']).RunState(config['output_dir']); \
build_idea(Path('ideas/$(slug).md'), config, state)"

# Remove all output but keep .spec.json files (re-run generate+write+build)
reset-generate:
	find output -name '.files.json' -delete
	find output -name '*.jsx' -delete
	find output -name '*.js' -not -name '.files.json' -delete

# Wipe everything
clean:
	rm -rf output/*/

help:
	@echo "Targets:"
	@echo "  make run           — full pipeline (LLM + docker build)"
	@echo "  make build-only    — LLM + write files, skip docker"
	@echo "  make slug=X one    — build a single idea"
	@echo "  make reset-generate — re-run generate+build for all"
	@echo "  make clean         — delete all output"
