/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * libFuzzer harness for eola_document_parse(). Every input the parser
 * accepts is rebuilt from its parsed type and fields, and the rebuilt text
 * must equal the input: an accepted document loses no octet and gains
 * none.
 */
#include <eola/document.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

static size_t append(char *buffer, size_t used, const char *text, size_t length)
{
	if (used + length > EOLA_DOCUMENT_MAX_LENGTH)
		abort();
	memcpy(buffer + used, text, length);
	return used + length;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	static char rebuilt[EOLA_DOCUMENT_MAX_LENGTH];
	struct eola_document document;
	struct eola_field field;
	size_t cursor = 0;
	size_t used = 0;

	if (eola_document_parse((const char *)data, size, &document) !=
	    EOLA_STATUS_OK)
		return 0;

	used = append(rebuilt, used, "EOLA1 ", 6);
	used = append(rebuilt, used, document.document_type,
		      document.document_type_length);
	used = append(rebuilt, used, "\n", 1);
	while (eola_document_next_field(&document, &cursor, &field)) {
		used = append(rebuilt, used, field.name, field.name_length);
		used = append(rebuilt, used, " ", 1);
		used = append(rebuilt, used, field.value, field.value_length);
		used = append(rebuilt, used, "\n", 1);
	}
	if (used != size || memcmp(rebuilt, data, size) != 0)
		abort();
	return 0;
}
