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
	}
	return NULL;
}
