/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * Encodings of field values, as specified in the Field Values section
 * of draft-wilczek-eola-signed-document.
 */
#ifndef EOLA_VALUE_H
#define EOLA_VALUE_H

#include <stddef.h>
#include <stdint.h>

#include <eola/status.h>

/**
 * eola_hex_value_decode() - decode a hexadecimal value of a known length
 * @text: the value, for example the value of a &struct eola_field
 * @text_length: the number of octets at @text
 * @octets: receives the decoded octets on success
 * @octets_length: the number of octets the value encodes, and the size of
 *	@octets
 *
 * Applies the value processing rules for a hexadecimal value of
 * @octets_length octets and stops at the first rule @text breaks. @octets
 * is written only on success.
 *
 * Return: EOLA_STATUS_OK, EOLA_STATUS_VALUE_HEX, EOLA_STATUS_VALUE_HEX_LENGTH,
 * or EOLA_STATUS_INVALID_ARGUMENT when @octets is NULL, @octets_length is 0,
 * or @text is NULL with a nonzero @text_length.
 */
enum eola_status eola_hex_value_decode(const char *text, size_t text_length,
				       unsigned char *octets,
				       size_t octets_length);

/**
 * eola_decimal_value_decode() - decode a decimal value
 * @text: the value, for example the value of a &struct eola_field
 * @text_length: the number of octets at @text
 * @value: receives the decoded integer on success
 *
 * Applies the value processing rules for a decimal value and stops at the
 * first rule @text breaks. @value is written only on success.
 *
 * Return: EOLA_STATUS_OK, EOLA_STATUS_VALUE_DECIMAL,
 * EOLA_STATUS_VALUE_DECIMAL_RANGE, or EOLA_STATUS_INVALID_ARGUMENT when
 * @value is NULL or @text is NULL with a nonzero @text_length.
 */
enum eola_status eola_decimal_value_decode(const char *text, size_t text_length,
					   uint64_t *value);

#endif /* EOLA_VALUE_H */
