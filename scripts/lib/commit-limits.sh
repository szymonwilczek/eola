# shellcheck shell=bash
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
#
# Commit message limits, shared by check-patch and format-patch.

export COMMIT_COLUMNS=75

# Body lines that keep their length: an indented line (a reproducer's
# commands and output), a trailer, or a line carrying a URL. ERE,
# read by awk and perl.
export COMMIT_LINE_EXEMPT='^[[:space:]]+[^[:space:]]|^[A-Za-z0-9-]+-by:|^(Fixes|Link):|[a-z][a-z0-9+.-]*://[^[:space:]]'
