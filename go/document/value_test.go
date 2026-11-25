// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

package document_test

import (
	"errors"
	"testing"

	"github.com/szymonwilczek/eola/go/document"
	"github.com/szymonwilczek/eola/go/status"
)

func TestDecodeHexValueOfNoOctets(t *testing.T) {
	_, err := document.DecodeHexValue("", 0)
	var code status.Code
	if err == nil || errors.As(err, &code) {
		t.Fatalf("expected an error that is not a status.Code, got %v", err)
	}
}
