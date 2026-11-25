/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * The processing rules of draft-wilczek-eola-signed-document, applied in
 * the order the draft gives them. Each check carries the number of its rule.
 */
#include <eola/document.h>

#include <string.h>

#define TYPE_LINE_MAGIC "EOLA"
#define TYPE_LINE_MAGIC_LENGTH (sizeof(TYPE_LINE_MAGIC) - 1)
#define TYPE_LINE_VERSION '1'

static bool is_digit(unsigned char octet)
{
	return octet >= '0' && octet <= '9';
}

static bool is_lowercase_letter(unsigned char octet)
{
	return octet >= 'a' && octet <= 'z';
}

/* LF, SP, or VCHAR. */
static bool is_document_octet(unsigned char octet)
{
	return octet == '\n' || (octet >= 0x20 && octet <= 0x7e);
}

/*
 * The rule name of the draft: a lowercase letter, then lowercase letters,
 * digits, and underscores.
 */
static bool is_name(const char *text, size_t length)
{
	size_t index;

	if (length == 0 || !is_lowercase_letter((unsigned char)text[0]))
		return false;
	for (index = 1; index < length; index++) {
		unsigned char octet = (unsigned char)text[index];

		if (!is_lowercase_letter(octet) && !is_digit(octet) &&
		    octet != '_')
			return false;
	}
	return true;
}

/* Rules 1 to 3: the document as a whole. */
static enum eola_status check_document(const char *text, size_t text_length)
{
	size_t index;

	if (text_length > EOLA_DOCUMENT_MAX_LENGTH)
		return EOLA_STATUS_DOCUMENT_TOO_LARGE;
	for (index = 0; index < text_length; index++) {
		if (!is_document_octet((unsigned char)text[index]))
			return EOLA_STATUS_DOCUMENT_CHARACTER;
	}
	if (text_length == 0 || text[text_length - 1] != '\n')
		return EOLA_STATUS_DOCUMENT_UNTERMINATED;
	return EOLA_STATUS_OK;
}

/* Rules 4 to 6, for a line of line_length octets with its LF. */
static enum eola_status check_line(const char *line, size_t line_length)
{
	if (line_length > EOLA_LINE_MAX_LENGTH)
		return EOLA_STATUS_LINE_TOO_LONG;
	if (line_length == 1)
		return EOLA_STATUS_LINE_EMPTY;
	if (line[line_length - 2] == ' ')
		return EOLA_STATUS_LINE_TRAILING_SPACE;
	return EOLA_STATUS_OK;
}

/* Rules 7 to 9, for the type line without its LF. */
static enum eola_status check_type_line(const char *line, size_t length,
					struct eola_document *document)
{
	size_t version_end = TYPE_LINE_MAGIC_LENGTH;

	if (length <= TYPE_LINE_MAGIC_LENGTH ||
	    memcmp(line, TYPE_LINE_MAGIC, TYPE_LINE_MAGIC_LENGTH) != 0 ||
	    !is_digit((unsigned char)line[TYPE_LINE_MAGIC_LENGTH]))
		return EOLA_STATUS_TYPE_LINE_MAGIC;

	while (version_end < length &&
	       is_digit((unsigned char)line[version_end]))
		version_end++;
	if (version_end != TYPE_LINE_MAGIC_LENGTH + 1 ||
	    line[TYPE_LINE_MAGIC_LENGTH] != TYPE_LINE_VERSION)
		return EOLA_STATUS_TYPE_LINE_VERSION;

	if (version_end == length || line[version_end] != ' ' ||
	    !is_name(line + version_end + 1, length - version_end - 1))
		return EOLA_STATUS_TYPE_LINE_DOCUMENT_TYPE;

	document->document_type = line + version_end + 1;
	document->document_type_length = length - version_end - 1;
	return EOLA_STATUS_OK;
}

/* Rules 10 to 12, for a field line without its LF. */
static enum eola_status check_field_line(const char *line, size_t length)
{
	const char *space = memchr(line, ' ', length);
	size_t name_length = space ? (size_t)(space - line) : length;

	if (!is_name(line, name_length))
		return EOLA_STATUS_FIELD_NAME;
	if (name_length == length)
		return EOLA_STATUS_FIELD_NO_VALUE;
	if (line[name_length + 1] == ' ')
		return EOLA_STATUS_FIELD_SEPARATOR;
	return EOLA_STATUS_OK;
}

enum eola_status eola_document_parse(const char *text, size_t text_length,
				     struct eola_document *document)
{
	struct eola_document parsed = {
		.text = text,
		.text_length = text_length,
	};
	enum eola_status status;
	size_t offset = 0;

	if (document == NULL || (text == NULL && text_length != 0))
		return EOLA_STATUS_INVALID_ARGUMENT;

	status = check_document(text, text_length);
	if (status != EOLA_STATUS_OK)
		return status;

	while (offset < text_length) {
		const char *line = text + offset;
		const char *line_feed =
			memchr(line, '\n', text_length - offset);
		size_t line_length = (size_t)(line_feed - line) + 1;

		status = check_line(line, line_length);
		if (status != EOLA_STATUS_OK)
			return status;

		if (offset == 0) {
			status =
				check_type_line(line, line_length - 1, &parsed);
			parsed.fields_offset = line_length;
		} else {
			status = check_field_line(line, line_length - 1);
		}
		if (status != EOLA_STATUS_OK)
			return status;

		offset += line_length;
	}

	*document = parsed;
	return EOLA_STATUS_OK;
}

bool eola_document_next_field(const struct eola_document *document,
			      size_t *cursor, struct eola_field *field)
{
	const char *line, *line_feed, *space;
	size_t offset;

	if (document == NULL || cursor == NULL || field == NULL)
		return false;

	offset = document->fields_offset + *cursor;
	if (offset >= document->text_length)
		return false;

	/*
	 * The document passed the processing rules, so every field line
	 * holds a name, one SP, and a value, and ends with LF.
	 */
	line = document->text + offset;
	line_feed = memchr(line, '\n', document->text_length - offset);
	space = memchr(line, ' ', (size_t)(line_feed - line));

	field->name = line;
	field->name_length = (size_t)(space - line);
	field->value = space + 1;
	field->value_length = (size_t)(line_feed - space - 1);
	*cursor += (size_t)(line_feed - line) + 1;
	return true;
}
