// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

package document_test

import (
	"bytes"
	"crypto/ed25519"
	"encoding/hex"
	"errors"
	"os"
	"path/filepath"
	"strconv"
	"testing"

	"github.com/szymonwilczek/eola/go/document"
	"github.com/szymonwilczek/eola/go/status"
)

// addVectorSeeds adds the content of every test vector to the seed corpus.
func addVectorSeeds(f *testing.F) {
	for _, vector := range readManifest(f) {
		text, err := os.ReadFile(filepath.Join(vectorDirectory, vector.file))
		if err != nil {
			f.Fatal(err)
		}
		f.Add(text)
	}
}

// isCode reports whether err is nil or a status.Code:
// every error a processing rule gives is a status.Code.
func isCode(err error) bool {
	var code status.Code
	return err == nil || errors.As(err, &code)
}

// FuzzParse checks that every document Parse accepts rebuilds to its
// input: an accepted document loses no octet and gains none.
func FuzzParse(f *testing.F) {
	addVectorSeeds(f)
	f.Fuzz(func(t *testing.T, text []byte) {
		parsed, err := document.Parse(text)
		if !isCode(err) {
			t.Fatalf("Parse returned an error that is not a status.Code: %v", err)
		}
		if err == nil && !bytes.Equal(rebuild(parsed), text) {
			t.Fatal("the parsed document does not rebuild to the input")
		}
	})
}

// FuzzDecodeValues decodes the input as a hexadecimal and a decimal value.
// A value either decoder accepts encodes back to the input, and the
// decimal decoder agrees with strconv.ParseUint on every input of digits
// without a leading zero.
func FuzzDecodeValues(f *testing.F) {
	addVectorSeeds(f)
	f.Fuzz(func(t *testing.T, input []byte) {
		text := string(input)

		length := max(len(text)/2, 1)
		octets, err := document.DecodeHexValue(text, length)
		if !isCode(err) {
			t.Fatalf("DecodeHexValue returned an error that is not a status.Code: %v", err)
		}
		if err == nil && hex.EncodeToString(octets) != text {
			t.Fatal("the decoded octets do not encode the input")
		}

		value, err := document.DecodeDecimalValue(text)
		if !isCode(err) {
			t.Fatalf("DecodeDecimalValue returned an error that is not a status.Code: %v", err)
		}
		if err == nil && strconv.FormatUint(value, 10) != text {
			t.Fatal("the decoded integer does not encode the input")
		}
		if !isCanonicalDigits(text) {
			if err == nil {
				t.Fatal("DecodeDecimalValue accepted a value that is not digits without a leading zero")
			}
			return
		}
		expected, parseErr := strconv.ParseUint(text, 10, 64)
		switch {
		case errors.Is(parseErr, strconv.ErrRange):
			if !errors.Is(err, status.ValueDecimalRange) {
				t.Fatalf("expected value_decimal_range, got %v", err)
			}
		case err != nil || value != expected:
			t.Fatalf("expected %d, got %d (%v)", expected, value, err)
		}
	})
}

// isCanonicalDigits reports whether text is digits without a leading zero.
func isCanonicalDigits(text string) bool {
	if text == "" || (len(text) > 1 && text[0] == '0') {
		return false
	}
	for index := range len(text) {
		if text[index] < '0' || text[index] > '9' {
			return false
		}
	}
	return true
}

// FuzzVerify checks Verify against Parse and Sign. With an expected type
// no document has, Verify gives the error of Parse, or
// document_type_unexpected for a document Parse accepts. With the type
// and the signer value of the document itself, Verify gives a status.Code,
// and an accepted document is the one Parse gives. A document Sign
// returns starts with the input and has two fields more; that it
// verifies, Sign checks itself.
func FuzzVerify(f *testing.F) {
	addVectorSeeds(f)
	key := ed25519.NewKeyFromSeed(make([]byte, ed25519.SeedSize))
	publicKey, _ := key.Public().(ed25519.PublicKey)
	f.Fuzz(func(t *testing.T, text []byte) {
		parsed, parseErr := document.Parse(text)
		_, err := document.Verify(text, "", publicKey)
		want := parseErr
		if parseErr == nil {
			want = status.DocumentTypeUnexpected
		}
		if !errors.Is(err, want) {
			t.Fatalf("Verify with an unexpected type gave %v, Parse %v", err, parseErr)
		}
		if parseErr != nil {
			return
		}

		signer := make(ed25519.PublicKey, ed25519.PublicKeySize)
		for _, field := range parsed.Fields {
			if field.Name == "signer" {
				if octets, err := document.DecodeHexValue(field.Value, ed25519.PublicKeySize); err == nil {
					signer = octets
				}
			}
		}
		verified, err := document.Verify(text, parsed.Type, signer)
		if !isCode(err) {
			t.Fatalf("Verify returned an error that is not a status.Code: %v", err)
		}
		if err == nil && !bytes.Equal(rebuild(verified), text) {
			t.Fatal("the verified document does not rebuild to the input")
		}

		signed, err := document.Sign(text, key)
		if err != nil {
			return
		}
		reparsed, err := document.Parse(signed)
		if err != nil {
			t.Fatalf("a signed document does not parse: %v", err)
		}
		if !bytes.HasPrefix(signed, text) ||
			len(reparsed.Fields) != len(parsed.Fields)+2 {
			t.Fatal("the signed document does not keep the fields of the input")
		}
	})
}
