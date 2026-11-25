/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * Ed25519 verification, the one part of libeola that calls OpenSSL.
 * The rest of the library reaches the cryptography only through this
 * header, so another backend replaces signature.c alone.
 */
#ifndef EOLA_SIGNATURE_H
#define EOLA_SIGNATURE_H

#include <stdbool.h>
#include <stddef.h>

#include <eola/document.h>
#include <eola/status.h>

/**
 * eola_signature_key_is_valid() - check a public key as rule 22 does
 * @public_key: the public key, EOLA_PUBLIC_KEY_LENGTH octets
 *
 * Return: false for the encodings that the Signer Keys section of
 * draft-wilczek-eola-signed-document lists: a y-coordinate not less than
 * p, x = 0 with the sign bit set, and the points of small order.
 */
bool eola_signature_key_is_valid(const unsigned char *public_key);

/**
 * eola_signature_verify() - verify an Ed25519 signature as rule 24 does
 * @public_key: the public key, EOLA_PUBLIC_KEY_LENGTH octets, that
 *	eola_signature_key_is_valid() accepts
 * @signature: the signature, EOLA_SIGNATURE_LENGTH octets
 * @message: the signed message
 * @message_length: the number of octets at @message
 *
 * Verifies with the choices of the Signature Processing Rules of
 * draft-wilczek-eola-signed-document: S less than L, R canonical,
 * the equation without the cofactor. The checks of the key are those
 * of eola_signature_key_is_valid(), which the caller has applied.
 *
 * Return: EOLA_STATUS_OK, EOLA_STATUS_SIGNATURE_INVALID, or
 * EOLA_STATUS_CRYPTO_FAILURE when OpenSSL fails for another reason.
 */
enum eola_status eola_signature_verify(const unsigned char *public_key,
				       const unsigned char *signature,
				       const char *message,
				       size_t message_length);

#endif /* EOLA_SIGNATURE_H */
