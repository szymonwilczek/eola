// SPDX-License-Identifier: MIT
// Copyright (C) 2026 Szymon Wilczek

package document

import (
	"errors"
	"math"

	"github.com/szymonwilczek/eola/go/status"
)

// errNoOctets reports a hexadecimal value asked for with no octets.
var errNoOctets = errors.New("document: a hexadecimal value encodes at least one octet")

// hexDigitValue returns the value of a lowercase hexadecimal digit, or -1.
func hexDigitValue(octet byte) int {
	switch {
	case isDigit(octet):
		return int(octet - '0')
	case octet >= 'a' && octet <= 'f':
		return int(octet-'a') + 10
	}
	return -1
}

// isHexValue reports whether text matches the rule hex-value:
// one or more pairs of lowercase hexadecimal digits.
func isHexValue(text string) bool {
	if text == "" || len(text)%2 != 0 {
		return false
	}
	for index := range len(text) {
		if hexDigitValue(text[index]) < 0 {
			return false
		}
	}
	return true
}

// isDecimalValue reports whether text matches the rule decimal-value:
// "0", or digits without a leading zero.
func isDecimalValue(text string) bool {
	if text == "" {
		return false
	}
	for index := range len(text) {
		if !isDigit(text[index]) {
			return false
		}
	}
	return len(text) == 1 || text[0] != '0'
}

// DecodeHexValue applies the value processing rules for a hexadecimal
// value of length octets, rules 13 and 14 of the draft, and returns the
// octets. The error is a status.Code, or an error that is not one when
// length is less than 1.
func DecodeHexValue(text string, length int) ([]byte, error) {
	if length < 1 {
		return nil, errNoOctets
	}
	if !isHexValue(text) {
		return nil, status.ValueHex
	}
	if len(text)/2 != length {
		return nil, status.ValueHexLength
	}

	octets := make([]byte, length)
	for index := range octets {
		high := hexDigitValue(text[2*index])
		low := hexDigitValue(text[2*index+1])
		octets[index] = byte(high<<4 | low)
	}
	return octets, nil
}

// DecodeDecimalValue applies the value processing rules for a decimal
// value, rules 15 and 16 of the draft, and returns the integer.
// The error is a status.Code.
func DecodeDecimalValue(text string) (uint64, error) {
	if !isDecimalValue(text) {
		return 0, status.ValueDecimal
	}

	var decoded uint64
	for index := range len(text) {
		digit := uint64(text[index] - '0')
		if decoded > (math.MaxUint64-digit)/10 {
			return 0, status.ValueDecimalRange
		}
		decoded = decoded*10 + digit
	}
	return decoded, nil
}
