// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

package document_test

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
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

// TestVectors runs the test vectors through Parse and rebuilds every valid
// document from its parsed type and fields to check that parsing loses no
// octet.
func TestVectors(t *testing.T) {
	for _, vector := range readManifest(t) {
		t.Run(vector.file, func(t *testing.T) {
			if vector.check != "document" {
				t.Fatalf("unknown check %s", vector.check)
			}
			text, err := os.ReadFile(filepath.Join(vectorDirectory, vector.file))
			if err != nil {
				t.Fatal(err)
			}
			parsed, err := document.Parse(text)
			if reported := resultName(err); reported != vector.result {
				t.Fatalf("expected %s, reported %s", vector.result, reported)
			}
			if err == nil && !bytes.Equal(rebuild(parsed), text) {
				t.Fatal("the parsed fields do not rebuild the document")
			}
		})
	}
}
