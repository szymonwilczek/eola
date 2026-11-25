// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

package document_test

import (
	"bytes"
	"encoding/hex"
	"errors"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"

	"github.com/szymonwilczek/eola/go/document"
	"github.com/szymonwilczek/eola/go/status"
)

const vectorDirectory = "../../vectors/signed-document"

type vector struct {
	file   string
	check  string
	result string
}

func readManifest(t *testing.T) []vector {
	t.Helper()
	manifest, err := os.ReadFile(filepath.Join(vectorDirectory, "vectors.txt"))
	if err != nil {
		t.Fatal(err)
	}

	var vectors []vector
	for _, line := range strings.Split(string(manifest), "\n") {
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Split(line, " ")
		if len(parts) != 3 {
			t.Fatalf("malformed manifest line: %q", line)
		}
		vectors = append(vectors, vector{parts[0], parts[1], parts[2]})
	}
	if len(vectors) == 0 {
		t.Fatal("the manifest lists no vectors")
	}
	return vectors
}

// rebuild writes a parsed document back into text form.
func rebuild(parsed *document.Document) []byte {
	var text bytes.Buffer
	text.WriteString("EOLA1 " + parsed.Type + "\n")
	for _, field := range parsed.Fields {
		text.WriteString(field.Name + " " + field.Value + "\n")
	}
	return text.Bytes()
}

func resultName(err error) string {
	if err == nil {
		return "ok"
	}
	var code status.Code
	if errors.As(err, &code) {
		return code.Name()
	}
	return err.Error()
}

// TestVectors runs the test vectors through Parse, DecodeHexValue and
// DecodeDecimalValue. Every valid document is rebuilt from its parsed type
// and fields, and every valid value is encoded again from what it decodes
// to, to check that decoding loses no octet.
func TestVectors(t *testing.T) {
	for _, vector := range readManifest(t) {
		t.Run(vector.file, func(t *testing.T) {
			text, err := os.ReadFile(filepath.Join(vectorDirectory, vector.file))
			if err != nil {
				t.Fatal(err)
			}
			var encoded []byte
			switch {
			case vector.check == "document":
				var parsed *document.Document
				parsed, err = document.Parse(text)
				if err == nil {
					encoded = rebuild(parsed)
				}
			case strings.HasPrefix(vector.check, "hex:"):
				length, convertErr := strconv.Atoi(strings.TrimPrefix(vector.check, "hex:"))
				if convertErr != nil {
					t.Fatalf("malformed check %s", vector.check)
				}
				var octets []byte
				octets, err = document.DecodeHexValue(string(text), length)
				encoded = []byte(hex.EncodeToString(octets))
			case vector.check == "decimal":
				var value uint64
				value, err = document.DecodeDecimalValue(string(text))
				encoded = strconv.AppendUint(nil, value, 10)
			default:
				t.Fatalf("unknown check %s", vector.check)
			}
			if reported := resultName(err); reported != vector.result {
				t.Fatalf("expected %s, reported %s", vector.result, reported)
			}
			if err == nil && !bytes.Equal(encoded, text) {
				t.Fatal("the decoded result does not encode the input again")
			}
		})
	}
}
