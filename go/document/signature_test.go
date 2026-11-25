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
	"strings"
	"testing"

	"github.com/szymonwilczek/eola/go/document"
	"github.com/szymonwilczek/eola/go/status"
)

// readTestKeys returns the private keys of test-keys.txt by their public
// key in hexadecimal.
func readTestKeys(t *testing.T) map[string]ed25519.PrivateKey {
	t.Helper()
	text, err := os.ReadFile(filepath.Join(vectorDirectory, "test-keys.txt"))
	if err != nil {
		t.Fatal(err)
	}
	keys := map[string]ed25519.PrivateKey{}
	for _, line := range strings.Split(string(text), "\n") {
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Split(line, " ")
		if len(parts) != 3 {
			t.Fatalf("malformed test key line: %q", line)
		}
		seed, err := hex.DecodeString(parts[1])
		if err != nil || len(seed) != ed25519.SeedSize {
			t.Fatalf("malformed seed of %s", parts[0])
		}
		key := ed25519.NewKeyFromSeed(seed)
		if public := hex.EncodeToString(key.Public().(ed25519.PublicKey)); public != parts[2] {
			t.Fatalf("the seed of %s gives the public key %s", parts[0], public)
		}
		keys[parts[2]] = key
	}
	if len(keys) == 0 {
		t.Fatal("test-keys.txt lists no keys")
	}
	return keys
}

// TestSignVectors signs each valid signed vector again, without its signer
// and signature lines, and compares the result with the vector: Ed25519
// signatures are deterministic, so Sign and the generator agree octet for
// octet.
func TestSignVectors(t *testing.T) {
	keys := readTestKeys(t)
	signed := 0
	for _, vector := range readManifest(t) {
		if !strings.HasPrefix(vector.check, "verify:") || vector.result != "ok" {
			continue
		}
		t.Run(vector.file, func(t *testing.T) {
			text, err := os.ReadFile(filepath.Join(vectorDirectory, vector.file))
			if err != nil {
				t.Fatal(err)
			}
			_, publicKey := parseVerifyCheck(t, vector.check)
			key, known := keys[hex.EncodeToString(publicKey)]
			if !known {
				t.Fatal("the signer is not a test key")
			}
			lines := bytes.SplitAfter(text, []byte("\n"))
			unsigned := bytes.Join(lines[:len(lines)-3], nil)
			result, err := document.Sign(unsigned, key)
			if err != nil {
				t.Fatal(err)
			}
			if !bytes.Equal(result, text) {
				t.Fatal("Sign does not give the vector")
			}
		})
		signed++
	}
	if signed == 0 {
		t.Fatal("the manifest lists no valid signed vector")
	}
}

func TestSignRejects(t *testing.T) {
	key := ed25519.NewKeyFromSeed(make([]byte, ed25519.SeedSize))
	signed, err := document.Sign([]byte("EOLA1 heartbeat\n"), key)
	if err != nil {
		t.Fatal(err)
	}

	cases := []struct {
		name     string
		unsigned []byte
		key      ed25519.PrivateKey
		code     status.Code
	}{
		{"a framing error", []byte("EOLA1 heartbeat\n\n"), key, status.LineEmpty},
		{"a signed document", signed, key, 0},
		{"a signer field", []byte("EOLA1 heartbeat\nsigner 00\n"), key, 0},
		{"a key of the wrong length", []byte("EOLA1 heartbeat\n"), key[:32], 0},
		{
			// 65456 octets, which the signer and signature lines take over
			// the limit.
			"a result over the limit",
			append([]byte("EOLA1 heartbeat\n"),
				bytes.Repeat([]byte("p "+strings.Repeat("x", 8177)+"\n"), 8)...),
			key, 0,
		},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			result, err := document.Sign(test.unsigned, test.key)
			if err == nil || result != nil {
				t.Fatal("Sign accepts it")
			}
			var code status.Code
			isCode := errors.As(err, &code)
			if test.code != 0 && (!isCode || code != test.code) {
				t.Fatalf("expected %s, reported %v", test.code.Name(), err)
			}
			if test.code == 0 && isCode {
				t.Fatalf("an argument error is the code %s", code.Name())
			}
		})
	}
}

func TestVerifyKeyLength(t *testing.T) {
	_, err := document.Verify([]byte("EOLA1 heartbeat\n"), "heartbeat", make([]byte, 31))
	var code status.Code
	if err == nil || errors.As(err, &code) {
		t.Fatalf("a key of 31 octets gives %v", err)
	}
}
