/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * Runs the test vectors of a manifest through libeola. Each vector is a
 * line "<file> <check> <result>"; the test reports every vector whose
 * result differs. Every valid document is rebuilt from its parsed type and
 * fields, and every valid value is encoded again from what it decodes to,
 * to check that decoding loses no octet. A verified document is rebuilt
 * too, its signer and signature fields included.
 *
 * Usage: vectors <directory of vectors.txt>
 */
#include <eola/document.h>
#include <eola/status.h>
#include <eola/value.h>

#include <openssl/crypto.h>

#include <inttypes.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MANIFEST_NAME "vectors.txt"
#define PATH_MAX_LENGTH 4096
#define MANIFEST_LINE_MAX_LENGTH 512
#define HEX_CHECK_PREFIX "hex:"
#define VERIFY_CHECK_PREFIX "verify:"
#define DECIMAL_TEXT_MAX_LENGTH 21

/*
 * Room for a file one octet longer than the largest document,
 * as the document_too_large vectors are, and one octet more to tell
 * a longer file.
 */
#define VECTOR_MAX_LENGTH (EOLA_DOCUMENT_MAX_LENGTH + 2)

static int read_file(const char *path, char *buffer, size_t buffer_size,
		     size_t *length)
{
	FILE *file = fopen(path, "rb");
	int result = -1;

	if (file == NULL) {
		fprintf(stderr, "%s: cannot open\n", path);
		return -1;
	}
	*length = fread(buffer, 1, buffer_size, file);
	if (ferror(file) || *length == buffer_size) {
		fprintf(stderr, "%s: cannot read, or larger than %zu octets\n",
			path, buffer_size - 1);
		goto out;
	}
	result = 0;
out:
	fclose(file);
	return result;
}

/*
 * Writes the type line and the fields of a parsed document back into
 * text form and compares the result with the parsed octets.
 */
static int document_round_trips(const struct eola_document *document,
				char *buffer, size_t buffer_size)
{
	struct eola_field field;
	size_t cursor = 0;
	int length;
	size_t used;

	length = snprintf(buffer, buffer_size, "EOLA1 %.*s\n",
			  (int)document->document_type_length,
			  document->document_type);
	if (length < 0 || (size_t)length >= buffer_size)
		return 0;
	used = (size_t)length;
	while (eola_document_next_field(document, &cursor, &field)) {
		length = snprintf(buffer + used, buffer_size - used,
				  "%.*s %.*s\n", (int)field.name_length,
				  field.name, (int)field.value_length,
				  field.value);
		if (length < 0 || (size_t)length >= buffer_size - used)
			return 0;
		used += (size_t)length;
	}
	return used == document->text_length &&
	       memcmp(buffer, document->text, used) == 0;
}

/* Reports a result that differs from the manifest; returns whether it does. */
static bool result_differs(const char *name, enum eola_status status,
			   const char *expected)
{
	const char *reported = eola_status_name(status);

	if (strcmp(reported, expected) == 0)
		return false;
	printf("FAIL %s: expected %s, reported %s\n", name, expected, reported);
	return true;
}

static int run_hex_vector(const char *name, const char *text,
			  size_t text_length, size_t octets_length,
			  const char *expected, unsigned char *octets)
{
	static const char digits[] = "0123456789abcdef";
	enum eola_status status;
	size_t index;

	status =
		eola_hex_value_decode(text, text_length, octets, octets_length);
	if (result_differs(name, status, expected))
		return -1;
	if (status != EOLA_STATUS_OK)
		return 0;
	for (index = 0; index < octets_length; index++) {
		if (text[2 * index] != digits[octets[index] >> 4] ||
		    text[2 * index + 1] != digits[octets[index] & 0x0f]) {
			printf("FAIL %s: the decoded octets do not encode the "
			       "value\n",
			       name);
			return -1;
		}
	}
	return 0;
}

static int run_decimal_vector(const char *name, const char *text,
			      size_t text_length, const char *expected)
{
	char encoded[DECIMAL_TEXT_MAX_LENGTH];
	enum eola_status status;
	uint64_t value;
	int length;

	status = eola_decimal_value_decode(text, text_length, &value);
	if (result_differs(name, status, expected))
		return -1;
	if (status != EOLA_STATUS_OK)
		return 0;
	length = snprintf(encoded, sizeof(encoded), "%" PRIu64, value);
	if (length < 0 || (size_t)length != text_length ||
	    memcmp(encoded, text, text_length) != 0) {
		printf("FAIL %s: the decoded integer does not encode the "
		       "value\n",
		       name);
		return -1;
	}
	return 0;
}

static int run_document_vector(const char *name, const char *text,
			       size_t text_length, const char *expected,
			       char *rebuilt, size_t rebuilt_size)
{
	struct eola_document document;
	enum eola_status status;

	status = eola_document_parse(text, text_length, &document);
	if (result_differs(name, status, expected))
		return -1;
	if (status == EOLA_STATUS_OK &&
	    !document_round_trips(&document, rebuilt, rebuilt_size)) {
		printf("FAIL %s: the parsed fields do not rebuild the "
		       "document\n",
		       name);
		return -1;
	}
	return 0;
}

/*
 * A check "verify:<type>:<key>": the key is the hexadecimal text of
 * EOLA_PUBLIC_KEY_LENGTH octets, as a signer value writes it.
 */
static int run_verify_vector(const char *name, const char *check,
			     const char *text, size_t text_length,
			     const char *expected, char *rebuilt,
			     size_t rebuilt_size)
{
	char expected_type[MANIFEST_LINE_MAX_LENGTH];
	unsigned char signer[EOLA_PUBLIC_KEY_LENGTH];
	struct eola_document document;
	const char *arguments = check + strlen(VERIFY_CHECK_PREFIX);
	const char *separator = strrchr(arguments, ':');
	enum eola_status status;
	size_t type_length;

	if (separator == NULL ||
	    eola_hex_value_decode(separator + 1, strlen(separator + 1), signer,
				  sizeof(signer)) != EOLA_STATUS_OK) {
		printf("FAIL %s: malformed check %s\n", name, check);
		return -1;
	}
	type_length = (size_t)(separator - arguments);
	memcpy(expected_type, arguments, type_length);
	expected_type[type_length] = '\0';

	status = eola_document_verify(text, text_length, expected_type, signer,
				      &document);
	if (result_differs(name, status, expected))
		return -1;
	if (status == EOLA_STATUS_OK &&
	    !document_round_trips(&document, rebuilt, rebuilt_size)) {
		printf("FAIL %s: the verified fields do not rebuild the "
		       "document\n",
		       name);
		return -1;
	}
	return 0;
}

int main(int argc, char **argv)
{
	static char text[VECTOR_MAX_LENGTH];
	static char rebuilt[VECTOR_MAX_LENGTH];
	char path[PATH_MAX_LENGTH];
	char line[MANIFEST_LINE_MAX_LENGTH];
	char name[MANIFEST_LINE_MAX_LENGTH], check[MANIFEST_LINE_MAX_LENGTH];
	char expected[MANIFEST_LINE_MAX_LENGTH];
	unsigned int vector_count = 0, failure_count = 0;
	size_t text_length;
	FILE *manifest;

	if (argc != 2) {
		fprintf(stderr, "usage: %s <vector directory>\n", argv[0]);
		return 2;
	}
	snprintf(path, sizeof(path), "%s/%s", argv[1], MANIFEST_NAME);
	manifest = fopen(path, "r");
	if (manifest == NULL) {
		fprintf(stderr, "%s: cannot open\n", path);
		return 2;
	}

	while (fgets(line, sizeof(line), manifest) != NULL) {
		if (line[0] == '#' || line[0] == '\n')
			continue;
		if (sscanf(line, "%511s %511s %511s", name, check, expected) !=
		    3) {
			fprintf(stderr, "%s: malformed line: %s", MANIFEST_NAME,
				line);
			failure_count++;
			continue;
		}
		vector_count++;
		snprintf(path, sizeof(path), "%s/%s", argv[1], name);
		if (read_file(path, text, sizeof(text), &text_length) != 0) {
			failure_count++;
			continue;
		}
		if (strcmp(check, "document") == 0) {
			if (run_document_vector(name, text, text_length,
						expected, rebuilt,
						sizeof(rebuilt)) != 0)
				failure_count++;
		} else if (strncmp(check, HEX_CHECK_PREFIX,
				   strlen(HEX_CHECK_PREFIX)) == 0) {
			size_t octets_length = (size_t)strtoul(
				check + strlen(HEX_CHECK_PREFIX), NULL, 10);

			if (octets_length == 0 ||
			    octets_length > sizeof(rebuilt) ||
			    run_hex_vector(name, text, text_length,
					   octets_length, expected,
					   (unsigned char *)rebuilt) != 0)
				failure_count++;
		} else if (strncmp(check, VERIFY_CHECK_PREFIX,
				   strlen(VERIFY_CHECK_PREFIX)) == 0) {
			if (run_verify_vector(name, check, text, text_length,
					      expected, rebuilt,
					      sizeof(rebuilt)) != 0)
				failure_count++;
		} else if (strcmp(check, "decimal") == 0) {
			if (run_decimal_vector(name, text, text_length,
					       expected) != 0)
				failure_count++;
		} else {
			printf("FAIL %s: unknown check %s\n", name, check);
			failure_count++;
		}
	}
	fclose(manifest);
	/*
	 * Free the state OpenSSL keeps for the process, so that valgrind
	 * reports any block the verification leaves as a leak.
	 */
	OPENSSL_cleanup();

	printf("%u vectors, %u failed\n", vector_count, failure_count);
	return failure_count == 0 && vector_count > 0 ? 0 : 1;
}
