// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

// Package status holds the error codes of the EOLA specifications.
//
// A Code is an error. Functions of the EOLA packages return a Code,
// so a caller compares with errors.Is or a type switch, and reports
// the code by its name or its number as the specifications give them.
package status

import "strconv"

// Code is an error code of the EOLA specifications.
type Code int

// Error codes of draft-wilczek-eola-signed-document,
// with the numbers of its Error Codes section.
const (
	DocumentTooLarge     Code = 101
	DocumentCharacter    Code = 102
	DocumentUnterminated Code = 103
	LineTooLong          Code = 104
	LineEmpty            Code = 105
	LineTrailingSpace    Code = 106
	TypeLineMagic        Code = 107
	TypeLineVersion      Code = 108
	TypeLineDocumentType Code = 109
	FieldName            Code = 110
	FieldNoValue         Code = 111
	FieldSeparator       Code = 112
)

var names = map[Code]string{
	DocumentTooLarge:     "document_too_large",
	DocumentCharacter:    "document_character",
	DocumentUnterminated: "document_unterminated",
	LineTooLong:          "line_too_long",
	LineEmpty:            "line_empty",
	LineTrailingSpace:    "line_trailing_space",
	TypeLineMagic:        "type_line_magic",
	TypeLineVersion:      "type_line_version",
	TypeLineDocumentType: "type_line_document_type",
	FieldName:            "field_name",
	FieldNoValue:         "field_no_value",
	FieldSeparator:       "field_separator",
}

// Name returns the name of the code as the specifications and test vectors
// write it, or an empty string for a value that is not a code.
func (code Code) Name() string {
	return names[code]
}

// Error returns the name of the code, or "eola error <number>" for a value
// that is not a code.
func (code Code) Error() string {
	if name, known := names[code]; known {
		return name
	}
	return "eola error " + strconv.Itoa(int(code))
}
