# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
#
# Build and tests of libeola. "make help" lists the targets.

.DEFAULT_GOAL := all

CC ?= cc
CLANG_FORMAT ?= clang-format
VALGRIND ?= valgrind
BUILD_DIR ?= build
VECTORS_DIR := ../vectors

# V=1 prints every command in full.
ifeq ($(V),1)
  QUIET_CC =
  QUIET_AR =
  QUIET_LD =
else
  QUIET_CC = @echo "  CC      $@";
  QUIET_AR = @echo "  AR      $@";
  QUIET_LD = @echo "  LD      $@";
endif

WARNINGS := -Wall -Wextra -Werror -Wpedantic -Wshadow -Wconversion \
	-Wsign-conversion -Wstrict-prototypes -Wmissing-prototypes \
	-Wcast-qual -Wvla -Wformat=2
CFLAGS ?= -O2 -g
EOLA_CFLAGS := -std=c11 $(WARNINGS) -Iinclude -MMD -MP

SANITIZE_FLAGS := -fsanitize=address,undefined -fno-sanitize-recover=all \
	-fno-omit-frame-pointer

LIBRARY_SOURCES := src/document.c src/status.c src/value.c
TEST_PROGRAMS := vectors arguments
C_SOURCES := $(LIBRARY_SOURCES) $(TEST_PROGRAMS:%=tests/%.c) \
	$(wildcard include/eola/*.h)

# Each build variant has its own directory: the plain build,
# and the build with AddressSanitizer and UndefinedBehaviorSanitizer.
define variant
$(1)_DIR := $(BUILD_DIR)/$(1)
$(1)_LIBRARY := $$($(1)_DIR)/libeola.a
$(1)_OBJECTS := $$(LIBRARY_SOURCES:src/%.c=$$($(1)_DIR)/%.o)
$(1)_TESTS := $$(TEST_PROGRAMS:%=$$($(1)_DIR)/tests/%)

$$($(1)_DIR)/%.o: src/%.c
	@mkdir -p $$(@D)
	$$(QUIET_CC)$$(CC) $$(EOLA_CFLAGS) $$(CFLAGS) $(2) -c -o $$@ $$<

$$($(1)_DIR)/tests/%.o: tests/%.c
	@mkdir -p $$(@D)
	$$(QUIET_CC)$$(CC) $$(EOLA_CFLAGS) $$(CFLAGS) $(2) -c -o $$@ $$<

$$($(1)_LIBRARY): $$($(1)_OBJECTS)
	$$(QUIET_AR)$$(AR) rcs $$@ $$^

$$($(1)_DIR)/tests/%: $$($(1)_DIR)/tests/%.o $$($(1)_LIBRARY)
	$$(QUIET_LD)$$(CC) $$(CFLAGS) $(2) -o $$@ $$^

-include $$(wildcard $$($(1)_DIR)/*.d $$($(1)_DIR)/tests/*.d)
endef

$(eval $(call variant,release,))
$(eval $(call variant,sanitize,$(SANITIZE_FLAGS)))

# Runs the test programs of a variant, with an optional command before each.
define run_tests
	$(1) $($(2)_DIR)/tests/vectors $(VECTORS_DIR)/signed-document
	$(1) $($(2)_DIR)/tests/arguments
endef

.PHONY: all check check-sanitize check-valgrind format format-check \
	clean help
.SECONDARY:

all: $(release_LIBRARY)

check: $(release_TESTS)
	$(call run_tests,,release)

check-sanitize: $(sanitize_TESTS)
	$(call run_tests,,sanitize)

check-valgrind: $(release_TESTS)
	$(call run_tests,$(VALGRIND) --quiet --error-exitcode=1 \
		--leak-check=full --errors-for-leak-kinds=all,release)

format:
	$(CLANG_FORMAT) -i $(C_SOURCES)

format-check:
	$(CLANG_FORMAT) --dry-run --Werror $(C_SOURCES)

clean:
	rm -rf $(BUILD_DIR)

help:
	@echo "Targets:"
	@echo "  all             build $(release_LIBRARY) (default)"
	@echo "  check           run the tests and the test vectors"
	@echo "  check-sanitize  run them with AddressSanitizer and"
	@echo "                  UndefinedBehaviorSanitizer"
	@echo "  check-valgrind  run them under valgrind"
	@echo "  format          format the C sources in place"
	@echo "  format-check    report C sources that are not formatted"
	@echo "  clean           remove $(BUILD_DIR)"
	@echo "  help            list the targets and the variables"
	@echo "Variables: CC, CFLAGS, BUILD_DIR, CLANG_FORMAT, VALGRIND, V=1 for"
	@echo "full commands."
