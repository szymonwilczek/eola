/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * Ed25519 verification through the EVP interface of OpenSSL. The checks
 * of the encodings run here, on the octets, before OpenSSL sees them,
 * so the result does not depend on what a release of OpenSSL tolerates.
 */
#include "signature.h"

#include <stdbool.h>
#include <string.h>

#include <openssl/evp.h>

#define ENCODING_LENGTH 32

/* L, the order of the base point, little-endian. */
static const unsigned char group_order[ENCODING_LENGTH] = {
	0xed, 0xd3, 0xf5, 0x5c, 0x1a, 0x63, 0x12, 0x58, 0xd6, 0x9c, 0xf7,
	0xa2, 0xde, 0xf9, 0xde, 0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10,
};

/*
 * The two points with x-coordinate 0, y = 1 and y = p - 1,
 * with the sign bit set: encodings that fail to decode.
 */
static const unsigned char negative_zero[][ENCODING_LENGTH] = {
	{0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80},
	{0xec, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
	 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
	 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff},
};

/* Whether the little-endian integer s is less than L. */
static bool is_below_group_order(const unsigned char *s)
{
	size_t index = ENCODING_LENGTH;

	while (index-- > 0) {
		if (s[index] != group_order[index])
			return s[index] < group_order[index];
	}
	return false;
}

/*
 * Whether the y-coordinate of an encoding, its low 255 bits, is less than
 * p = 2^255 - 19: it is not when the bits are all ones but for a lowest
 * octet of at least 0xed.
 */
static bool is_canonical_y(const unsigned char *encoding)
{
	size_t index;

	if ((encoding[ENCODING_LENGTH - 1] & 0x7f) != 0x7f)
		return true;
	for (index = 1; index < ENCODING_LENGTH - 1; index++) {
		if (encoding[index] != 0xff)
			return true;
	}
	return encoding[0] < 0xed;
}

/*
 * The checks of RFC 8032, Section 5.1.3, that need no arithmetic.
 * A point that is not on the curve fails in OpenSSL;
 * R is compared there as octets, after the equation is computed.
 */
static bool is_decodable(const unsigned char *encoding)
{
	size_t index;

	if (!is_canonical_y(encoding))
		return false;
	for (index = 0;
	     index < sizeof(negative_zero) / sizeof(negative_zero[0]);
	     index++) {
		if (memcmp(encoding, negative_zero[index], ENCODING_LENGTH) ==
		    0)
			return false;
	}
	return true;
}

enum eola_status eola_signature_verify(const unsigned char *public_key,
				       const unsigned char *signature,
				       const char *message,
				       size_t message_length)
{
	enum eola_status status = EOLA_STATUS_CRYPTO_FAILURE;
	EVP_MD_CTX *context = NULL;
	EVP_PKEY *key;
	int result;

	if (!is_decodable(public_key) || !is_decodable(signature) ||
	    !is_below_group_order(signature + ENCODING_LENGTH))
		return EOLA_STATUS_SIGNATURE_INVALID;

	key = EVP_PKEY_new_raw_public_key(EVP_PKEY_ED25519, NULL, public_key,
					  EOLA_PUBLIC_KEY_LENGTH);
	if (key == NULL)
		return EOLA_STATUS_CRYPTO_FAILURE;
	context = EVP_MD_CTX_new();
	if (context == NULL ||
	    EVP_DigestVerifyInit(context, NULL, NULL, NULL, key) != 1)
		goto out;

	/* 1 for a valid signature, 0 for an invalid one, below 0 on failure. */
	result = EVP_DigestVerify(context, signature, EOLA_SIGNATURE_LENGTH,
				  (const unsigned char *)message,
				  message_length);
	if (result == 1)
		status = EOLA_STATUS_OK;
	else if (result == 0)
		status = EOLA_STATUS_SIGNATURE_INVALID;
out:
	EVP_MD_CTX_free(context);
	EVP_PKEY_free(key);
	return status;
}
