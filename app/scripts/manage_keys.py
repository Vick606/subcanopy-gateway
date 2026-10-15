# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

"""API key management CLI.

Usage:
    uv run python -m app.scripts.manage_keys create --name "my app"
    uv run python -m app.scripts.manage_keys list
    uv run python -m app.scripts.manage_keys deactivate <key-id>
    uv run python -m app.scripts.manage_keys activate <key-id>

The raw key is printed once at creation and never stored. Only the
HMAC-SHA256 hash lives in the database.
"""

import asyncio
import uuid

import typer
from sqlalchemy import select

from app.config import get_settings
from app.database import create_engine, create_session_factory
from app.models.api_key import APIKey
from app.security import generate_api_key, hash_api_key

cli = typer.Typer(
    help="Manage API keys for the gateway.",
    no_args_is_help=True,
)


async def _create(name: str) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    raw_key = generate_api_key()
    record = APIKey(
        id=uuid.uuid4(),
        name=name,
        key_hash=hash_api_key(raw_key, settings.api_key_pepper.encode()),
        is_active=True,
    )

    async with session_factory() as session:
        session.add(record)
        await session.commit()

    await engine.dispose()

    typer.echo("")
    typer.echo("API key created. Store it now, it will not be shown again.")
    typer.echo("")
    typer.echo(f"  id:    {record.id}")
    typer.echo(f"  name:  {record.name}")
    typer.echo(f"  key:   {raw_key}")
    typer.echo("")


async def _list() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        stmt = select(APIKey).order_by(APIKey.created_at.desc())
        records = (await session.execute(stmt)).scalars().all()

    await engine.dispose()

    if not records:
        typer.echo("No API keys.")
        return

    typer.echo(
        f"{'id':<10} {'name':<24} {'active':<7} "
        f"{'created':<20} {'last used':<20}"
    )
    typer.echo("-" * 85)
    for r in records:
        last_used = (
            r.last_used_at.strftime("%Y-%m-%d %H:%M:%S")
            if r.last_used_at
            else "-"
        )
        created = r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        active = "yes" if r.is_active else "no"
        typer.echo(
            f"{str(r.id)[:8]:<10} {r.name[:23]:<24} {active:<7} "
            f"{created:<20} {last_used:<20}"
        )


async def _set_active(key_id: str, active: bool) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    try:
        uid = uuid.UUID(key_id)
    except ValueError:
        typer.echo(f"Invalid key id: {key_id}", err=True)
        await engine.dispose()
        raise typer.Exit(code=1)

    async with session_factory() as session:
        record = await session.get(APIKey, uid)
        if record is None:
            typer.echo(f"No key with id {key_id}", err=True)
            await engine.dispose()
            raise typer.Exit(code=1)
        record.is_active = active
        await session.commit()
        name = record.name

    await engine.dispose()

    state = "activated" if active else "deactivated"
    typer.echo(f"{state}: {key_id} ({name})")


@cli.command()
def create(
    name: str = typer.Option(
        ..., "--name", "-n", help="Human-readable name for this key."
    ),
) -> None:
    """Create a new API key. The raw key is shown once and never stored."""
    asyncio.run(_create(name))


@cli.command("list")
def list_keys() -> None:
    """List all API keys."""
    asyncio.run(_list())


@cli.command()
def deactivate(key_id: str = typer.Argument(..., help="Key UUID.")) -> None:
    """Mark a key inactive. It will be rejected on the next request."""
    asyncio.run(_set_active(key_id, active=False))


@cli.command()
def activate(key_id: str = typer.Argument(..., help="Key UUID.")) -> None:
    """Reactivate a previously deactivated key."""
    asyncio.run(_set_active(key_id, active=True))


if __name__ == "__main__":
    cli()
