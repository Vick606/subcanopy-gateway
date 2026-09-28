# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from fastapi.testclient import TestClient

from app.config import Settings


def test_version_returns_settings(client: TestClient, settings: Settings) -> None:
    response = client.get("/version")

    assert response.status_code == 200
    body = response.json()
    assert body["app"] == settings.app_name
    assert body["version"] == settings.version
