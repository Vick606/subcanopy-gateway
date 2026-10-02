# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from app.scripts.seed import DATA_PATH, load_patterns


def test_load_patterns_returns_list_of_dicts() -> None:
    patterns = load_patterns(DATA_PATH)

    assert len(patterns) > 1000
    first = patterns[0]
    assert "name" in first
    assert "text" in first
    assert "source_corpus" in first
    assert "category" in first


def test_load_patterns_has_both_corpora() -> None:
    patterns = load_patterns(DATA_PATH)

    sources = {p["source_corpus"] for p in patterns}

    assert sources == {"agentdojo", "promptwall"}


def test_load_patterns_names_are_unique() -> None:
    patterns = load_patterns(DATA_PATH)

    names = [p["name"] for p in patterns]

    assert len(names) == len(set(names))
