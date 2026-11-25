/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * libFuzzer harness for eola_hex_value_decode() and
 * eola_decimal_value_decode(). The input is decoded both ways. A value
 * either decoder accepts must encode back to the input, and the decimal
 * decoder must agree with strtoull() on every input of digits without a
 * leading zero.
 */
#include <eola/value.h>

#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HEX_MAX_OCTETS 4096
#define DECIMAL_ENCODED_MAX_LENGTH 21

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

static void check_hex(const char *text, size_t size)
{
	static const char digits[] = "0123456789abcdef";
	static unsigned char octets[HEX_MAX_OCTETS];
	size_t octets_length = size / 2 > 0 ? size / 2 : 1;
	size_t index;

	if (octets_length > HEX_MAX_OCTETS)
		return;
	if (eola_hex_value_decode(text, size, octets, octets_length) !=
	    EOLA_STATUS_OK)
		return;
	if (size != 2 * octets_length)
		abort();
	for (index = 0; index < octets_length; index++) {
		if (text[2 * index] != digits[octets[index] >> 4] ||
		    text[2 * index + 1] != digits[octets[index] & 0x0f])
			abort();
	}
}

static int is_canonical_digits(const char *text, size_t size)
{
	size_t index;

	if (size == 0 || (size > 1 && text[0] == '0'))
		return 0;
	for (index = 0; index < size; index++) {
		if (text[index] < '0' || text[index] > '9')
			return 0;
	}
	return 1;
}

static void check_decimal(const char *text, size_t size)
{
	char encoded[DECIMAL_ENCODED_MAX_LENGTH];
	char *terminated;
	unsigned long long expected;
	bool out_of_range;
	enum eola_status status;
	uint64_t value;

	status = eola_decimal_value_decode(text, size, &value);
	if (status == EOLA_STATUS_OK) {
		int length =
			snprintf(encoded, sizeof(encoded), "%" PRIu64, value);

		if (length < 0 || (size_t)length != size ||
		    memcmp(encoded, text, size) != 0)
			abort();
	}

	if (!is_canonical_digits(text, size)) {
		if (status == EOLA_STATUS_OK)
			abort();
		return;
	}
	terminated = malloc(size + 1);
	if (terminated == NULL)
		abort();
	memcpy(terminated, text, size);
	terminated[size] = '\0';
	errno = 0;
	expected = strtoull(terminated, NULL, 10);
	out_of_range = errno == ERANGE;
	free(terminated);
	if (out_of_range) {
		if (status != EOLA_STATUS_VALUE_DECIMAL_RANGE)
			abort();
	} else if (status != EOLA_STATUS_OK || value != expected) {
		abort();
	}
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	check_hex((const char *)data, size);
	check_decimal((const char *)data, size);
	return 0;
}
