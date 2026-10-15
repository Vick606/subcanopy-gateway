# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from app.security import (
    KEY_PREFIX,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)

PEPPER = b"test-pepper-at-least-32-bytes-long!"


def test_generate_api_key_has_prefix() -> None:
    key = generate_api_key()

    assert key.startswith(KEY_PREFIX)
    assert len(key) > 40


def test_generate_api_key_is_unique() -> None:
    keys = {generate_api_key() for _ in range(100)}

    assert len(keys) == 100


def test_hash_api_key_is_deterministic() -> None:
    key = generate_api_key()

    assert hash_api_key(key, PEPPER) == hash_api_key(key, PEPPER)


def test_hash_api_key_is_hex_sha256() -> None:
    digest = hash_api_key("scg_test", PEPPER)

    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_hash_api_key_changes_with_pepper() -> None:
    key = generate_api_key()

    assert hash_api_key(key, PEPPER) != hash_api_key(key, b"other-pepper")


def test_verify_api_key_accepts_match() -> None:
    key = generate_api_key()
    stored = hash_api_key(key, PEPPER)

    assert verify_api_key(key, stored, PEPPER) is True


def test_verify_api_key_rejects_wrong_key() -> None:
    key = generate_api_key()
    stored = hash_api_key(key, PEPPER)

    assert verify_api_key("scg_wrong", stored, PEPPER) is False


def test_verify_api_key_rejects_wrong_pepper() -> None:
    key = generate_api_key()
    stored = hash_api_key(key, PEPPER)

    assert verify_api_key(key, stored, b"wrong-pepper") is False
