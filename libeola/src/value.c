/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * The value processing rules of draft-wilczek-eola-signed-document,
 * rules 13 to 16, applied in the order the draft gives them.
 */
#include <eola/value.h>

#include <stdbool.h>

static bool is_digit(unsigned char octet)
{
	return octet >= '0' && octet <= '9';
}

/* The digit value of a lowercase hexadecimal digit, or -1. */
static int hex_digit_value(unsigned char octet)
{
	if (is_digit(octet))
		return octet - '0';
	if (octet >= 'a' && octet <= 'f')
		return octet - 'a' + 10;
	return -1;
}

/* The rule hex-value: one or more pairs of lowercase hexadecimal digits. */
static bool is_hex_value(const char *text, size_t text_length)
{
	size_t index;

	if (text_length == 0 || text_length % 2 != 0)
		return false;
	for (index = 0; index < text_length; index++) {
		if (hex_digit_value((unsigned char)text[index]) < 0)
			return false;
	}
	return true;
}

/* The rule decimal-value: "0", or digits without a leading zero. */
static bool is_decimal_value(const char *text, size_t text_length)
{
	size_t index;

	if (text_length == 0)
		return false;
	for (index = 0; index < text_length; index++) {
		if (!is_digit((unsigned char)text[index]))
			return false;
	}
	return text_length == 1 || text[0] != '0';
}

enum eola_status eola_hex_value_decode(const char *text, size_t text_length,
				       unsigned char *octets,
				       size_t octets_length)
{
	size_t index;

	if (octets == NULL || octets_length == 0 ||
	    (text == NULL && text_length != 0))
		return EOLA_STATUS_INVALID_ARGUMENT;

	/* Rule 13. */
	if (!is_hex_value(text, text_length))
		return EOLA_STATUS_VALUE_HEX;
	/* Rule 14; text_length is even, so the halving loses nothing. */
	if (text_length / 2 != octets_length)
		return EOLA_STATUS_VALUE_HEX_LENGTH;

	for (index = 0; index < octets_length; index++) {
		int high = hex_digit_value((unsigned char)text[2 * index]);
		int low = hex_digit_value((unsigned char)text[2 * index + 1]);

		octets[index] = (unsigned char)(high << 4 | low);
	}
	return EOLA_STATUS_OK;
}

enum eola_status eola_decimal_value_decode(const char *text, size_t text_length,
					   uint64_t *value)
{
	uint64_t decoded = 0;
	size_t index;

	if (value == NULL || (text == NULL && text_length != 0))
		return EOLA_STATUS_INVALID_ARGUMENT;

	/* Rule 15. */
	if (!is_decimal_value(text, text_length))
		return EOLA_STATUS_VALUE_DECIMAL;

	/* Rule 16: stop before the integer would exceed UINT64_MAX. */
	for (index = 0; index < text_length; index++) {
		uint64_t digit = (uint64_t)(text[index] - '0');

		if (decoded > (UINT64_MAX - digit) / 10)
			return EOLA_STATUS_VALUE_DECIMAL_RANGE;
		decoded = decoded * 10 + digit;
	}
	*value = decoded;
	return EOLA_STATUS_OK;
}
