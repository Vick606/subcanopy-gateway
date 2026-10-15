# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

"""API key generation, hashing, and verification.

API keys are high-entropy random tokens, not user passwords. The
hashing strategy reflects that: HMAC-SHA256 with a server-side pepper
is fast, constant-time comparable, and resists rainbow-table attacks.
Argon2 would add ~100ms per request with no security gain against a
256-bit random key.
"""

import hashlib
import hmac
import secrets

KEY_PREFIX = "scg_"
KEY_BYTES = 32


def generate_api_key() -> str:
    """Return a new API key: scg_ + 32 bytes of URL-safe randomness."""
    return KEY_PREFIX + secrets.token_urlsafe(KEY_BYTES)


def hash_api_key(raw_key: str, pepper: bytes) -> str:
    """Return the HMAC-SHA256 hex digest of the key.

    The pepper comes from SCG_API_KEY_PEPPER. Without it, an attacker
    with database access could precompute hashes for known key formats.
    """
    return hmac.new(
        pepper, raw_key.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_api_key(
    raw_key: str, stored_hash: str, pepper: bytes
) -> bool:
    """Constant-time verification of a raw key against a stored hash."""
    computed = hash_api_key(raw_key, pepper)
    return secrets.compare_digest(computed, stored_hash)
