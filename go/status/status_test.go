// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

package status_test

import (
	"errors"
	"fmt"
	"testing"

	"github.com/szymonwilczek/eola/go/status"
)

func TestWrappedCodeMatches(t *testing.T) {
	wrapped := fmt.Errorf("heartbeat: %w", status.LineEmpty)
	if !errors.Is(wrapped, status.LineEmpty) {
		t.Fatal("errors.Is does not find the wrapped code")
	}
	if errors.Is(wrapped, status.LineTooLong) {
		t.Fatal("errors.Is matches a different code")
	}
}

func TestUnknownCode(t *testing.T) {
	unknown := status.Code(99)
	if unknown.Name() != "" {
		t.Fatalf("a value that is not a code has the name %q", unknown.Name())
	}
	if unknown.Error() != "eola error 99" {
		t.Fatalf("unexpected error text %q", unknown.Error())
	}
}
