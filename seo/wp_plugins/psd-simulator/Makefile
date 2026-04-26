PIPELINE_NAME := psd-simulator

ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)
  BUILDER_PATH ?= /usr/builder
else
  BUILDER_PATH ?= $(HOME)/work/projects/builder
endif

STACK     := react
WEBAPP_DIR := webapp

include $(BUILDER_PATH)/Makefile

.PHONY: zip deploy

zip: build
	@echo "Zipping plugin for WordPress upload..."
	@cd plugin && zip -r ../psd-simulator.zip . -x "*.DS_Store" -x "__MACOSX/*"
	@echo "Created psd-simulator.zip — upload via WP Admin → Plugins → Add New"

deploy:
	@if [ -z "$(DEPLOY_USER)" ] || [ -z "$(DEPLOY_HOST)" ] || [ -z "$(DEPLOY_PATH)" ]; then \
		echo "Set DEPLOY_USER, DEPLOY_HOST, DEPLOY_PATH in Makefile.local first"; exit 1; \
	fi
	rsync -avz --delete plugin/ $(DEPLOY_USER)@$(DEPLOY_HOST):$(DEPLOY_PATH)/
