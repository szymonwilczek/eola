/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
#include <eola/status.h>

#include <stddef.h>

const char *eola_status_name(enum eola_status status)
{
	switch (status) {
	case EOLA_STATUS_OK:
		return "ok";
	case EOLA_STATUS_INVALID_ARGUMENT:
		return "invalid_argument";
	case EOLA_STATUS_CRYPTO_FAILURE:
		return "crypto_failure";
	case EOLA_STATUS_DOCUMENT_TOO_LARGE:
		return "document_too_large";
	case EOLA_STATUS_DOCUMENT_CHARACTER:
		return "document_character";
	case EOLA_STATUS_DOCUMENT_UNTERMINATED:
		return "document_unterminated";
	case EOLA_STATUS_LINE_TOO_LONG:
		return "line_too_long";
	case EOLA_STATUS_LINE_EMPTY:
		return "line_empty";
	case EOLA_STATUS_LINE_TRAILING_SPACE:
		return "line_trailing_space";
	case EOLA_STATUS_TYPE_LINE_MAGIC:
		return "type_line_magic";
	case EOLA_STATUS_TYPE_LINE_VERSION:
		return "type_line_version";
	case EOLA_STATUS_TYPE_LINE_DOCUMENT_TYPE:
		return "type_line_document_type";
	case EOLA_STATUS_FIELD_NAME:
		return "field_name";
	case EOLA_STATUS_FIELD_NO_VALUE:
		return "field_no_value";
	case EOLA_STATUS_FIELD_SEPARATOR:
		return "field_separator";
	case EOLA_STATUS_DOCUMENT_TYPE_UNEXPECTED:
		return "document_type_unexpected";
	case EOLA_STATUS_VALUE_HEX:
		return "value_hex";
	case EOLA_STATUS_VALUE_HEX_LENGTH:
		return "value_hex_length";
	case EOLA_STATUS_VALUE_DECIMAL:
		return "value_decimal";
	case EOLA_STATUS_VALUE_DECIMAL_RANGE:
		return "value_decimal_range";
	case EOLA_STATUS_SIGNATURE_MISSING:
		return "signature_missing";
	case EOLA_STATUS_SIGNATURE_POSITION:
		return "signature_position";
	case EOLA_STATUS_SIGNER_MISSING:
		return "signer_missing";
	case EOLA_STATUS_SIGNER_POSITION:
		return "signer_position";
	case EOLA_STATUS_SIGNER_KEY_INVALID:
		return "signer_key_invalid";
	case EOLA_STATUS_SIGNER_UNEXPECTED:
		return "signer_unexpected";
	case EOLA_STATUS_SIGNATURE_INVALID:
		return "signature_invalid";
	}
	return NULL;
}
