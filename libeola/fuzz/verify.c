/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * libFuzzer harness for eola_document_verify(). The expected document
 * type and signer are taken from the input itself, so that an input
 * reaches the signature check of rule 24 and OpenSSL without first
 * guessing them. For every input:
 *
 * - a document that breaks rules 1 to 12 gives the code eola_document_parse()
 *   gives, and a document that passes them gives document_type_unexpected
 *   for a type no document has;
 * - EOLA_STATUS_CRYPTO_FAILURE never happens, since the sanitizers do not
 *   make allocations fail;
 * - an accepted document is the one eola_document_parse() gives, and ends
 *   with the fields signer and signature.
 *
 * OpenSSL is not built with the sanitizers, so a read past the message
 * inside OpenSSL is not seen here; the valid test vectors catch a wrong
 * message length.
 */
#include <eola/document.h>
#include <eola/status.h>
#include <eola/value.h>

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

static int field_is(const struct eola_field *field, const char *name)
{
	return field->name_length == strlen(name) &&
	       memcmp(field->name, name, field->name_length) == 0;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	static char expected_type[EOLA_LINE_MAX_LENGTH];
	unsigned char signer[EOLA_PUBLIC_KEY_LENGTH] = {0};
	struct eola_document parsed, verified;
	struct eola_field field, before_last = {0}, last = {0};
	const char *text = (const char *)data;
	enum eola_status parse_status, status;
	size_t cursor = 0;

	parse_status = eola_document_parse(text, size, &parsed);
	/* No document type is empty, so "" is never the expected type. */
	status = eola_document_verify(text, size, "", signer, &verified);
	if (status != (parse_status == EOLA_STATUS_OK
			       ? EOLA_STATUS_DOCUMENT_TYPE_UNEXPECTED
			       : parse_status))
		abort();
	if (parse_status != EOLA_STATUS_OK)
		return 0;

	memcpy(expected_type, parsed.document_type,
	       parsed.document_type_length);
	expected_type[parsed.document_type_length] = '\0';
	while (eola_document_next_field(&parsed, &cursor, &field)) {
		if (field_is(&field, "signer"))
			eola_hex_value_decode(field.value, field.value_length,
					      signer, sizeof(signer));
		before_last = last;
		last = field;
	}

	status = eola_document_verify(text, size, expected_type, signer,
				      &verified);
	if (status == EOLA_STATUS_CRYPTO_FAILURE)
		abort();
	if (status != EOLA_STATUS_OK)
		return 0;
	if (memcmp(&verified, &parsed, sizeof(parsed)) != 0 ||
	    !field_is(&before_last, "signer") || !field_is(&last, "signature"))
		abort();
	return 0;
}
