// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

// Package document parses the framing of EOLA documents,
// as specified in draft-wilczek-eola-signed-document.
package document

import (
	"bytes"

	"github.com/szymonwilczek/eola/go/status"
)

const (
	// MaxDocumentLength is the largest document, in octets.
	MaxDocumentLength = 65536
	// MaxLineLength is the largest line, in octets, its LF included.
	MaxLineLength = 8192
)

const (
	typeLineMagic   = "EOLA"
	typeLineVersion = '1'
)

// Field is one field of a document.
type Field struct {
	Name  string
	Value string
}

// Document is a document that passed the processing rules.
type Document struct {
	// Type is the document type of the type line.
	Type string
	// Fields are the fields in the order of the document.
	Fields []Field
}

// Parse applies the processing rules of draft-wilczek-eola-signed-document
// in their order and stops at the first rule text breaks.
// The error is a status.Code.
func Parse(text []byte) (*Document, error) {
	if code := checkDocument(text); code != 0 {
		return nil, code
	}

	parsed := &Document{}
	for offset := 0; offset < len(text); {
		lineLength := bytes.IndexByte(text[offset:], '\n') + 1
		line := text[offset : offset+lineLength]
		if code := checkLine(line); code != 0 {
			return nil, code
		}

		content := line[:lineLength-1]
		if offset == 0 {
			documentType, code := checkTypeLine(content)
			if code != 0 {
				return nil, code
			}
			parsed.Type = documentType
		} else {
			field, code := checkFieldLine(content)
			if code != 0 {
				return nil, code
			}
			parsed.Fields = append(parsed.Fields, field)
		}
		offset += lineLength
	}
	return parsed, nil
}

func isDigit(octet byte) bool {
	return octet >= '0' && octet <= '9'
}

func isLowercaseLetter(octet byte) bool {
	return octet >= 'a' && octet <= 'z'
}

// isDocumentOctet reports whether octet is LF, SP, or VCHAR.
func isDocumentOctet(octet byte) bool {
	return octet == '\n' || (octet >= 0x20 && octet <= 0x7e)
}

// isName reports whether text matches the rule name of the draft:
// a lowercase letter, then lowercase letters, digits, and underscores.
func isName(text []byte) bool {
	if len(text) == 0 || !isLowercaseLetter(text[0]) {
		return false
	}
	for _, octet := range text[1:] {
		if !isLowercaseLetter(octet) && !isDigit(octet) && octet != '_' {
			return false
		}
	}
	return true
}

// checkDocument applies rules 1 to 3 to the document as a whole.
func checkDocument(text []byte) status.Code {
	if len(text) > MaxDocumentLength {
		return status.DocumentTooLarge
	}
	for _, octet := range text {
		if !isDocumentOctet(octet) {
			return status.DocumentCharacter
		}
	}
	if len(text) == 0 || text[len(text)-1] != '\n' {
		return status.DocumentUnterminated
	}
	return 0
}

// checkLine applies rules 4 to 6 to a line with its LF.
func checkLine(line []byte) status.Code {
	switch {
	case len(line) > MaxLineLength:
		return status.LineTooLong
	case len(line) == 1:
		return status.LineEmpty
	case line[len(line)-2] == ' ':
		return status.LineTrailingSpace
	}
	return 0
}

// checkTypeLine applies rules 7 to 9 to the type line without its LF
// and returns the document type.
func checkTypeLine(line []byte) (string, status.Code) {
	magicLength := len(typeLineMagic)
	if len(line) <= magicLength ||
		!bytes.HasPrefix(line, []byte(typeLineMagic)) ||
		!isDigit(line[magicLength]) {
		return "", status.TypeLineMagic
	}

	versionEnd := magicLength
	for versionEnd < len(line) && isDigit(line[versionEnd]) {
		versionEnd++
	}
	if versionEnd != magicLength+1 || line[magicLength] != typeLineVersion {
		return "", status.TypeLineVersion
	}

	if versionEnd == len(line) || line[versionEnd] != ' ' ||
		!isName(line[versionEnd+1:]) {
		return "", status.TypeLineDocumentType
	}
	return string(line[versionEnd+1:]), 0
}

// checkFieldLine applies rules 10 to 12 to a field line without its LF
// and returns the field.
func checkFieldLine(line []byte) (Field, status.Code) {
	nameLength := bytes.IndexByte(line, ' ')
	if nameLength < 0 {
		nameLength = len(line)
	}
	if !isName(line[:nameLength]) {
		return Field{}, status.FieldName
	}
	if nameLength == len(line) {
		return Field{}, status.FieldNoValue
	}
	if line[nameLength+1] == ' ' {
		return Field{}, status.FieldSeparator
	}
	return Field{
		Name:  string(line[:nameLength]),
		Value: string(line[nameLength+1:]),
	}, 0
}
