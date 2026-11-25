/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * Checks the behaviour of the public functions at the edges that the test
 * vectors do not reach: arguments that are NULL, and the empty document
 * passed as a NULL pointer.
 */
#include <eola/document.h>
#include <eola/status.h>
#include <eola/value.h>

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static unsigned int failure_count;

static void expect(int condition, const char *description)
{
	if (!condition) {
		printf("FAIL %s\n", description);
		failure_count++;
	}
}

int main(void)
{
	static const char text[] = "EOLA1 heartbeat\nsequence 1\n";
	struct eola_document document, untouched;
	struct eola_field field;
	unsigned char octets[2] = {0x5a, 0x5a};
	uint64_t value = 7;
	size_t cursor = 0;

	expect(eola_document_parse(text, sizeof(text) - 1, NULL) ==
		       EOLA_STATUS_INVALID_ARGUMENT,
	       "parse without a document to write is an invalid argument");
	expect(eola_document_parse(NULL, 1, &document) ==
		       EOLA_STATUS_INVALID_ARGUMENT,
	       "parse of NULL text with a length is an invalid argument");
	expect(eola_document_parse(NULL, 0, &document) ==
		       EOLA_STATUS_DOCUMENT_UNTERMINATED,
	       "parse of NULL text of length 0 is the empty document");

	memset(&document, 0x5a, sizeof(document));
	memcpy(&untouched, &document, sizeof(document));
	expect(eola_document_parse("EOLA1 x", 7, &document) ==
			       EOLA_STATUS_DOCUMENT_UNTERMINATED &&
		       memcmp(&document, &untouched, sizeof(document)) == 0,
	       "a failed parse leaves the document untouched");

	expect(eola_document_parse(text, sizeof(text) - 1, &document) ==
		       EOLA_STATUS_OK,
	       "parse of a valid document succeeds");
	expect(!eola_document_next_field(NULL, &cursor, &field),
	       "next field without a document reads nothing");
	expect(!eola_document_next_field(&document, NULL, &field),
	       "next field without a cursor reads nothing");
	expect(!eola_document_next_field(&document, &cursor, NULL),
	       "next field without a field to write reads nothing");
	expect(cursor == 0, "a rejected call leaves the cursor in place");
	expect(eola_document_next_field(&document, &cursor, &field) &&
		       !eola_document_next_field(&document, &cursor, &field),
	       "the one field is read once");

	expect(eola_hex_value_decode("00", 2, NULL, 1) ==
		       EOLA_STATUS_INVALID_ARGUMENT,
	       "hex decode without octets to write is an invalid argument");
	expect(eola_hex_value_decode("", 0, octets, 0) ==
		       EOLA_STATUS_INVALID_ARGUMENT,
	       "hex decode of zero octets is an invalid argument");
	expect(eola_hex_value_decode(NULL, 2, octets, 1) ==
		       EOLA_STATUS_INVALID_ARGUMENT,
	       "hex decode of NULL text with a length is an invalid argument");
	expect(eola_hex_value_decode("0g", 2, octets, 1) ==
			       EOLA_STATUS_VALUE_HEX &&
		       octets[0] == 0x5a,
	       "a failed hex decode leaves the octets untouched");
	expect(eola_hex_value_decode("ffff", 4, octets, 1) ==
			       EOLA_STATUS_VALUE_HEX_LENGTH &&
		       octets[0] == 0x5a,
	       "a hex decode of the wrong length leaves the octets untouched");
	expect(eola_hex_value_decode("ff", 2, octets, 1) == EOLA_STATUS_OK &&
		       octets[0] == 0xff && octets[1] == 0x5a,
	       "hex decode writes only the octets the value encodes");

	expect(eola_decimal_value_decode("1", 1, NULL) ==
		       EOLA_STATUS_INVALID_ARGUMENT,
	       "decimal decode without a value to write is an invalid "
	       "argument");
	expect(eola_decimal_value_decode(NULL, 1, &value) ==
		       EOLA_STATUS_INVALID_ARGUMENT,
	       "decimal decode of NULL text with a length is an invalid "
	       "argument");
	expect(eola_decimal_value_decode("01", 2, &value) ==
			       EOLA_STATUS_VALUE_DECIMAL &&
		       value == 7,
	       "a failed decimal decode leaves the value untouched");

	expect(eola_status_name((enum eola_status)99) == NULL,
	       "a value that is not a status code has no name");

	printf("%u failed\n", failure_count);
	return failure_count == 0 ? 0 : 1;
}
