# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
#
# Makefile for the specification drafts
#
# Each draft-*.md is converted by kramdown-rfc to RFCXML and rendered by
# xml2rfc to plain text and HTML under build/.
# Referenced RFCs are fetched once and cached in build/.refcache.

KRAMDOWN_RFC ?= kramdown-rfc
XML2RFC      ?= xml2rfc
BUILDDIR      = build

DRAFTS = $(wildcard draft-*.md)
XML    = $(patsubst %.md,$(BUILDDIR)/%.xml,$(DRAFTS))
TXT    = $(XML:.xml=.txt)
HTML   = $(XML:.xml=.html)

.PHONY: all clean
.SECONDARY: $(XML)

all: $(TXT) $(HTML)

$(BUILDDIR)/%.xml: %.md
	@mkdir -p $(BUILDDIR)/.refcache
	KRAMDOWN_REFCACHEDIR=$(BUILDDIR)/.refcache $(KRAMDOWN_RFC) $< >$@.tmp
	@mv $@.tmp $@

# xml2rfc reports layout and reference problems as warnings and still exits
# with status 0; a warning fails the build here.
$(BUILDDIR)/%.txt: $(BUILDDIR)/%.xml
	$(XML2RFC) --no-network --text -o $@ $< >$@.log 2>&1 || { cat $@.log; exit 1; }
	@if grep 'Warning:' $@.log; then rm -f $@; exit 1; fi

$(BUILDDIR)/%.html: $(BUILDDIR)/%.xml
	$(XML2RFC) --no-network --quiet --html -o $@ $<

clean:
	@rm -rf $(BUILDDIR)
