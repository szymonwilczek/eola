// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

package document

import (
	"bytes"
	"crypto/ed25519"
	"encoding/hex"
	"errors"

	"github.com/szymonwilczek/eola/go/status"
)

const (
	signerName    = "signer"
	signatureName = "signature"
)

var (
	// errKeyLength reports a public or private key of the wrong length.
	errKeyLength = errors.New("document: an Ed25519 key of the wrong length")
	// errReservedField reports a document to sign that already names a
	// field signer or signature.
	errReservedField = errors.New("document: the document to sign has a signer or signature field")
	// errSignedTooLarge reports a document that is too large once signed.
	errSignedTooLarge = errors.New("document: the signed document is larger than MaxDocumentLength")
)

// groupOrder is L, the order of the base point, little-endian.
var groupOrder = [32]byte{
	0xed, 0xd3, 0xf5, 0x5c, 0x1a, 0x63, 0x12, 0x58, 0xd6, 0x9c, 0xf7,
	0xa2, 0xde, 0xf9, 0xde, 0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10,
}

// isBelowGroupOrder reports whether the little-endian integer s
// is less than L.
func isBelowGroupOrder(s []byte) bool {
	for index := len(groupOrder) - 1; index >= 0; index-- {
		if s[index] != groupOrder[index] {
			return s[index] < groupOrder[index]
		}
	}
	return false
}

// isDecodable reports whether an encoding passes the checks of RFC 8032,
// Section 5.1.3, that need no arithmetic: a y-coordinate less than p,
// and no sign bit on x = 0. crypto/ed25519 decodes the rest.
func isDecodable(encoding []byte) bool {
	allOnes := encoding[31]&0x7f == 0x7f &&
		bytes.Count(encoding[1:31], []byte{0xff}) == 30
	if allOnes && encoding[0] >= 0xed {
		return false
	}
	// The two points with x = 0, y = 1 and y = p - 1, with the sign bit.
	negativeOne := allOnes && encoding[31] == 0xff && encoding[0] == 0xec
	negativeZeroOne := encoding[0] == 0x01 && encoding[31] == 0x80 &&
		bytes.Count(encoding[1:31], []byte{0x00}) == 30
	return !negativeOne && !negativeZeroOne
}

// verifySignature applies rule 23 with the choices of the Signature
// Processing Rules: S less than L, A and R canonical, the equation
// without the cofactor, which crypto/ed25519 checks.
func verifySignature(publicKey, signature, message []byte) bool {
	return isDecodable(publicKey) && isDecodable(signature[:32]) &&
		isBelowGroupOrder(signature[32:]) &&
		ed25519.Verify(publicKey, message, signature)
}

// checkReservedFields applies rules 18 to 21 to the fields of a document.
func checkReservedFields(fields []Field) status.Code {
	var signers, signatures int
	for _, field := range fields {
		switch field.Name {
		case signerName:
			signers++
		case signatureName:
			signatures++
		}
	}
	last := len(fields) - 1
	switch {
	case signatures == 0:
		return status.SignatureMissing
	case signatures != 1 || fields[last].Name != signatureName:
		return status.SignaturePosition
	case signers == 0:
		return status.SignerMissing
	// The only signer is not the last field, so last is at least 1.
	case signers != 1 || fields[last-1].Name != signerName:
		return status.SignerPosition
	}
	return 0
}

// Verify applies the processing rules and the signature processing rules
// of draft-wilczek-eola-signed-document in their order, and stops at the
// first rule text breaks; the error is then a status.Code. The last two
// fields of the document are signer and signature. An error that is not
// a status.Code reports an expectedSigner of the wrong length.
func Verify(text []byte, expectedType string, expectedSigner ed25519.PublicKey) (*Document, error) {
	if len(expectedSigner) != ed25519.PublicKeySize {
		return nil, errKeyLength
	}
	parsed, err := Parse(text)
	if err != nil {
		return nil, err
	}

	// Rule 17.
	if parsed.Type != expectedType {
		return nil, status.DocumentTypeUnexpected
	}
	if code := checkReservedFields(parsed.Fields); code != 0 {
		return nil, code
	}

	// Rules 13 and 14, for the signer value and then the signature value.
	last := len(parsed.Fields) - 1
	publicKey, err := DecodeHexValue(parsed.Fields[last-1].Value, ed25519.PublicKeySize)
	if err != nil {
		return nil, err
	}
	signatureValue := parsed.Fields[last].Value
	signature, err := DecodeHexValue(signatureValue, ed25519.SignatureSize)
	if err != nil {
		return nil, err
	}

	// Rule 22.
	if !bytes.Equal(publicKey, expectedSigner) {
		return nil, status.SignerUnexpected
	}

	// Rule 23. The signed message is every octet before the signature line.
	signatureLineLength := len(signatureName) + 1 + len(signatureValue) + 1
	if !verifySignature(publicKey, signature, text[:len(text)-signatureLineLength]) {
		return nil, status.SignatureInvalid
	}
	return parsed, nil
}

// Sign returns a document that is unsigned with the signer and signature
// fields of privateKey added, as Verify accepts it. unsigned is a document
// that passes the processing rules and has no signer or signature field;
// otherwise the error is the status.Code of the first rule it breaks,
// or an error that is not a status.Code.
func Sign(unsigned []byte, privateKey ed25519.PrivateKey) ([]byte, error) {
	if len(privateKey) != ed25519.PrivateKeySize {
		return nil, errKeyLength
	}
	parsed, err := Parse(unsigned)
	if err != nil {
		return nil, err
	}
	for _, field := range parsed.Fields {
		if field.Name == signerName || field.Name == signatureName {
			return nil, errReservedField
		}
	}

	publicKey, _ := privateKey.Public().(ed25519.PublicKey)
	signed := make([]byte, 0, len(unsigned)+256)
	signed = append(signed, unsigned...)
	signed = append(signed, signerName+" "+hex.EncodeToString(publicKey)+"\n"...)
	signature := ed25519.Sign(privateKey, signed)
	signed = append(signed, signatureName+" "+hex.EncodeToString(signature)+"\n"...)
	if len(signed) > MaxDocumentLength {
		return nil, errSignedTooLarge
	}

	if _, err := Verify(signed, parsed.Type, publicKey); err != nil {
		return nil, err
	}
	return signed, nil
}
