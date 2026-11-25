# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
#
# Build and tests of libeola. "make help" lists the targets.

.DEFAULT_GOAL := all

CC ?= cc
CLANG ?= clang
CLANG_FORMAT ?= clang-format
VALGRIND ?= valgrind
PKG_CONFIG ?= pkg-config
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

# libcrypto of OpenSSL, found with pkg-config unless set.
OPENSSL_CFLAGS ?= $(shell $(PKG_CONFIG) --cflags libcrypto)
OPENSSL_LIBS ?= $(shell $(PKG_CONFIG) --libs libcrypto)

SANITIZE_FLAGS := -fsanitize=address,undefined -fno-sanitize-recover=all \
	-fno-omit-frame-pointer

LIBRARY_SOURCES := src/document.c src/signature.c src/status.c src/value.c \
	src/verify.c
TEST_PROGRAMS := vectors arguments
FUZZ_TARGETS := document value
C_SOURCES := $(LIBRARY_SOURCES) $(TEST_PROGRAMS:%=tests/%.c) \
	$(FUZZ_TARGETS:%=fuzz/%.c) $(wildcard include/eola/*.h src/*.h)

# The fuzz targets are built with clang, libFuzzer and both sanitizers.
# "make fuzz-run" seeds each corpus with the test vectors and runs each
# target for FUZZ_SECONDS.
FUZZ_DIR := $(BUILD_DIR)/fuzz
FUZZ_FLAGS := -fsanitize=fuzzer,address,undefined \
	-fno-sanitize-recover=all -fno-omit-frame-pointer
FUZZ_PROGRAMS := $(FUZZ_TARGETS:%=$(FUZZ_DIR)/%)
FUZZ_SECONDS ?= 60
FUZZ_MAX_LENGTH := 65540

# Each build variant has its own directory: the plain build,
# and the build with AddressSanitizer and UndefinedBehaviorSanitizer.
define variant
$(1)_DIR := $(BUILD_DIR)/$(1)
$(1)_LIBRARY := $$($(1)_DIR)/libeola.a
$(1)_OBJECTS := $$(LIBRARY_SOURCES:src/%.c=$$($(1)_DIR)/%.o)
$(1)_TESTS := $$(TEST_PROGRAMS:%=$$($(1)_DIR)/tests/%)

$$($(1)_DIR)/%.o: src/%.c
	@mkdir -p $$(@D)
	$$(QUIET_CC)$$(CC) $$(EOLA_CFLAGS) $$(OPENSSL_CFLAGS) $$(CFLAGS) $(2) \
		-c -o $$@ $$<

$$($(1)_DIR)/tests/%.o: tests/%.c
	@mkdir -p $$(@D)
	$$(QUIET_CC)$$(CC) $$(EOLA_CFLAGS) $$(OPENSSL_CFLAGS) $$(CFLAGS) $(2) \
		-c -o $$@ $$<

$$($(1)_LIBRARY): $$($(1)_OBJECTS)
	$$(QUIET_AR)$$(AR) rcs $$@ $$^

$$($(1)_DIR)/tests/%: $$($(1)_DIR)/tests/%.o $$($(1)_LIBRARY)
	$$(QUIET_LD)$$(CC) $$(CFLAGS) $(2) -o $$@ $$^ $$(OPENSSL_LIBS)

-include $$(wildcard $$($(1)_DIR)/*.d $$($(1)_DIR)/tests/*.d)
endef

$(eval $(call variant,release,))
$(eval $(call variant,sanitize,$(SANITIZE_FLAGS)))

# Runs the test programs of a variant, with an optional command before each.
define run_tests
	$(1) $($(2)_DIR)/tests/vectors $(VECTORS_DIR)/signed-document
	$(1) $($(2)_DIR)/tests/arguments
endef

.PHONY: all check check-sanitize check-valgrind fuzz fuzz-run format \
	format-check clean help
.SECONDARY:

all: $(release_LIBRARY)

check: $(release_TESTS)
	$(call run_tests,,release)

check-sanitize: $(sanitize_TESTS)
	$(call run_tests,,sanitize)

check-valgrind: $(release_TESTS)
	$(call run_tests,$(VALGRIND) --quiet --error-exitcode=1 \
		--leak-check=full --errors-for-leak-kinds=all,release)

$(FUZZ_DIR)/%: fuzz/%.c $(LIBRARY_SOURCES) $(wildcard include/eola/*.h src/*.h)
	@mkdir -p $(@D)
	$(QUIET_CC)$(CLANG) $(EOLA_CFLAGS) $(OPENSSL_CFLAGS) $(CFLAGS) \
		$(FUZZ_FLAGS) -o $@ $< $(LIBRARY_SOURCES) $(OPENSSL_LIBS)

fuzz: $(FUZZ_PROGRAMS)

fuzz-run: $(FUZZ_PROGRAMS)
	@for target in $(FUZZ_TARGETS); do \
		corpus=$(FUZZ_DIR)/corpus/$$target; \
		mkdir -p $$corpus $(FUZZ_DIR)/crashes; \
		cp $(VECTORS_DIR)/*/*.eola $$corpus/ || exit 1; \
		echo "  FUZZ    $$target for $(FUZZ_SECONDS) s"; \
		$(FUZZ_DIR)/$$target -max_total_time=$(FUZZ_SECONDS) \
			-max_len=$(FUZZ_MAX_LENGTH) -print_final_stats=1 \
			-artifact_prefix=$(FUZZ_DIR)/crashes/$$target- \
			$$corpus || exit 1; \
	done

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
	@echo "  fuzz            build the libFuzzer targets with clang"
	@echo "  fuzz-run        run each for FUZZ_SECONDS (default 60),"
	@echo "                  seeded with the test vectors"
	@echo "  format          format the C sources in place"
	@echo "  format-check    report C sources that are not formatted"
	@echo "  clean           remove $(BUILD_DIR)"
	@echo "  help            list the targets and the variables"
	@echo "Variables: CC, CLANG, CFLAGS, BUILD_DIR, CLANG_FORMAT, VALGRIND,"
	@echo "FUZZ_SECONDS, PKG_CONFIG, OPENSSL_CFLAGS, OPENSSL_LIBS, V=1 for"
	@echo "full commands."
