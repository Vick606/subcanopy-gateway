# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

"""Smoke test that the CLI module imports and builds its command tree."""

from typer.testing import CliRunner

from app.scripts.manage_keys import cli

runner = CliRunner()


def test_cli_shows_help_on_no_args() -> None:
    result = runner.invoke(cli, [])

    assert result.exit_code == 0
    assert "Manage API keys" in result.output


def test_cli_lists_commands() -> None:
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    for command in ("create", "list", "deactivate", "activate"):
        assert command in result.output


def test_deactivate_rejects_invalid_uuid() -> None:
    result = runner.invoke(cli, ["deactivate", "not-a-uuid"])

    assert result.exit_code == 1
    assert "Invalid key id" in result.output
