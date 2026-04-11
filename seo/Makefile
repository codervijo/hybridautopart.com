ifeq ($(shell [ -f /.dockerenv ] && echo yes),yes)
  BUILDER_PATH ?= /usr/builder
else
  BUILDER_PATH ?= $(HOME)/work/projects/builder
endif
include $(BUILDER_PATH)/Makefile

PROJECT_NAME := seo-blog-generator
PYTHON       := python3
