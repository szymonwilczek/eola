/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * Framing of EOLA documents, as specified in
 * draft-wilczek-eola-signed-document. A parsed document points into
 * the buffer of the caller; nothing is allocated or copied.
 */
#ifndef EOLA_DOCUMENT_H
#define EOLA_DOCUMENT_H

#include <stdbool.h>
#include <stddef.h>

#include <eola/status.h>

/* Largest document, in octets. */
#define EOLA_DOCUMENT_MAX_LENGTH 65536

/* Largest line, in octets, its LF included. */
#define EOLA_LINE_MAX_LENGTH 8192

/**
 * struct eola_document - a document that passed the processing rules
 * @text: the first octet of the document, in the buffer of the caller
 * @text_length: the length of the document, in octets
 * @document_type: the document type, in @text; not terminated by NUL
 * @document_type_length: the length of @document_type, in octets
 * @fields_offset: the offset in @text of the first field line, or
 *	@text_length when the document has no fields
 *
 * The members stay valid as long as the buffer that holds the document.
 */
struct eola_document {
	const char *text;
	size_t text_length;
	const char *document_type;
	size_t document_type_length;
	size_t fields_offset;
};

/**
 * struct eola_field - one field of a document
 * @name: the field name, in the text of the document; not terminated by NUL
 * @name_length: the length of @name, in octets
 * @value: the field value, in the text of the document; not terminated by
 *	NUL
 * @value_length: the length of @value, in octets
 */
struct eola_field {
	const char *name;
	size_t name_length;
	const char *value;
	size_t value_length;
};

/**
 * eola_document_parse() - check a document against the processing rules
 * @text: the octets of the document
 * @text_length: the number of octets at @text
 * @document: receives the parsed document on success
 *
 * Applies the processing rules of draft-wilczek-eola-signed-document in
 * their order and stops at the first rule @text breaks. @document is
 * written only on success. @text can be NULL when @text_length is 0.
 *
 * Return: EOLA_STATUS_OK, the error code of the first rule @text breaks,
 * or EOLA_STATUS_INVALID_ARGUMENT when @document is NULL or @text is NULL
 * with a nonzero @text_length.
 */
enum eola_status eola_document_parse(const char *text, size_t text_length,
				     struct eola_document *document);

/**
 * eola_document_next_field() - read the next field of a document
 * @document: a document from eola_document_parse()
 * @cursor: the position of the next field; set it to 0 before the first
 *	call, and the function advances it
 * @field: receives the field
 *
 * Fields are read in the order of the document.
 *
 * Return: true when @field holds the next field, or false when no field is
 * left or @document, @cursor or @field is NULL; @cursor and @field are then
 * not written.
 */
bool eola_document_next_field(const struct eola_document *document,
			      size_t *cursor, struct eola_field *field);

#endif /* EOLA_DOCUMENT_H */
