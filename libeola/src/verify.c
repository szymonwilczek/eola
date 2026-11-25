/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * The signature processing rules of draft-wilczek-eola-signed-document,
 * rules 17 to 24, applied in the order the draft gives them after rules 1
 * to 12. Each check carries the number of its rule.
 */
#include <eola/document.h>
#include <eola/value.h>

#include <stdbool.h>
#include <string.h>

#include "signature.h"

#define SIGNER_NAME "signer"
#define SIGNATURE_NAME "signature"

static bool field_is(const struct eola_field *field, const char *name)
{
	size_t name_length = strlen(name);

	return field->name_length == name_length &&
	       memcmp(field->name, name, name_length) == 0;
}

/* The fields that rules 18 to 21 look at. */
struct reserved_fields {
	size_t field_count;
	size_t signer_count;
	size_t signature_count;
	struct eola_field before_last;
	struct eola_field last;
};

static void find_reserved_fields(const struct eola_document *document,
				 struct reserved_fields *found)
{
	struct eola_field field;
	size_t cursor = 0;

	memset(found, 0, sizeof(*found));
	while (eola_document_next_field(document, &cursor, &field)) {
		found->field_count++;
		if (field_is(&field, SIGNER_NAME))
			found->signer_count++;
		if (field_is(&field, SIGNATURE_NAME))
			found->signature_count++;
		found->before_last = found->last;
		found->last = field;
	}
}

/* Rules 18 to 21. */
static enum eola_status check_positions(const struct reserved_fields *found)
{
	if (found->signature_count == 0)
		return EOLA_STATUS_SIGNATURE_MISSING;
	if (found->signature_count != 1 ||
	    !field_is(&found->last, SIGNATURE_NAME))
		return EOLA_STATUS_SIGNATURE_POSITION;
	if (found->signer_count == 0)
		return EOLA_STATUS_SIGNER_MISSING;
	/*
	 * The only signer is not the last field, which is the signature,
	 * so the document has a field before the last.
	 */
	if (found->signer_count != 1 ||
	    !field_is(&found->before_last, SIGNER_NAME))
		return EOLA_STATUS_SIGNER_POSITION;
	return EOLA_STATUS_OK;
}

enum eola_status eola_document_verify(const char *text, size_t text_length,
				      const char *expected_type,
				      const unsigned char *expected_signer,
				      struct eola_document *document)
{
	unsigned char public_key[EOLA_PUBLIC_KEY_LENGTH];
	unsigned char signature[EOLA_SIGNATURE_LENGTH];
	struct reserved_fields found;
	struct eola_document parsed;
	enum eola_status status;

	if (expected_type == NULL || expected_signer == NULL ||
	    document == NULL || (text == NULL && text_length != 0))
		return EOLA_STATUS_INVALID_ARGUMENT;

	status = eola_document_parse(text, text_length, &parsed);
	if (status != EOLA_STATUS_OK)
		return status;

	/* Rule 17. */
	if (parsed.document_type_length != strlen(expected_type) ||
	    memcmp(parsed.document_type, expected_type,
		   parsed.document_type_length) != 0)
		return EOLA_STATUS_DOCUMENT_TYPE_UNEXPECTED;

	find_reserved_fields(&parsed, &found);
	status = check_positions(&found);
	if (status != EOLA_STATUS_OK)
		return status;

	/* Rules 13 and 14, for the signer value and then the signature. */
	status = eola_hex_value_decode(found.before_last.value,
				       found.before_last.value_length,
				       public_key, sizeof(public_key));
	if (status != EOLA_STATUS_OK)
		return status;
	status =
		eola_hex_value_decode(found.last.value, found.last.value_length,
				      signature, sizeof(signature));
	if (status != EOLA_STATUS_OK)
		return status;

	/* Rule 22. */
	if (!eola_signature_key_is_valid(public_key))
		return EOLA_STATUS_SIGNER_KEY_INVALID;

	/* Rule 23. */
	if (memcmp(public_key, expected_signer, sizeof(public_key)) != 0)
		return EOLA_STATUS_SIGNER_UNEXPECTED;

	/*
	 * Rule 24. The signed message ends with the LF before the signature
	 * line, and the name of the last field starts that line.
	 */
	status = eola_signature_verify(public_key, signature, text,
				       (size_t)(found.last.name - text));
	if (status != EOLA_STATUS_OK)
		return status;

	*document = parsed;
	return EOLA_STATUS_OK;
}
