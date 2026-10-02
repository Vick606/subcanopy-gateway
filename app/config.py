# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SCG_",
        extra="ignore",
    )

    app_name: str = "subcanopy-gateway"
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://scg:scg@localhost:5432/scg"


def get_settings() -> Settings:
    return Settings()
