from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)

DB_DIR = Path("db")


async def _execute_many(db_path: Path, statements: list[str]) -> None:
    DB_DIR.mkdir(exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        for statement in statements:
            await db.execute(statement)
        await db.commit()


async def run_startup_migrations() -> None:
    """Create missing tables used by startup checks without changing data."""
    await _execute_many(
        DB_DIR / "prefix.db",
        [
            """
            CREATE TABLE IF NOT EXISTS prefixes (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT NOT NULL
            )
            """,
        ],
    )

    await _execute_many(
        DB_DIR / "np.db",
        [
            """
            CREATE TABLE IF NOT EXISTS np (
                id INTEGER PRIMARY KEY,
                expiry_time TEXT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS autonp (
                guild_id INTEGER PRIMARY KEY
            )
            """,
        ],
    )

    async with aiosqlite.connect(DB_DIR / "np.db") as db:
        async with db.execute("PRAGMA table_info(np)") as cursor:
            columns = {row[1] for row in await cursor.fetchall()}
        if "expiry_time" not in columns:
            await db.execute("ALTER TABLE np ADD COLUMN expiry_time TEXT NULL")
        await db.commit()

    await _execute_many(
        DB_DIR / "block.db",
        [
            """
            CREATE TABLE IF NOT EXISTS user_blacklist (
                user_id TEXT PRIMARY KEY,
                timestamp TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS guild_blacklist (
                guild_id TEXT PRIMARY KEY,
                timestamp TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER
            )
            """,
        ],
    )

    await _execute_many(
        DB_DIR / "ignore.db",
        [
            "CREATE TABLE IF NOT EXISTS ignored_commands (guild_id INTEGER, command_name TEXT)",
            "CREATE TABLE IF NOT EXISTS ignored_channels (guild_id INTEGER, channel_id INTEGER)",
            "CREATE TABLE IF NOT EXISTS ignored_users (guild_id INTEGER, user_id INTEGER)",
            "CREATE TABLE IF NOT EXISTS bypassed_users (guild_id INTEGER, user_id INTEGER)",
        ],
    )

    await _execute_many(
        DB_DIR / "topcheck.db",
        [
            """
            CREATE TABLE IF NOT EXISTS topcheck (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 0
            )
            """,
        ],
    )

    await _execute_many(
        DB_DIR / "automod.db",
        [
            """
            CREATE TABLE IF NOT EXISTS automod (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS automod_punishments (
                guild_id INTEGER,
                event TEXT,
                punishment TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS automod_ignored (
                guild_id INTEGER,
                type TEXT,
                id INTEGER
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS automod_logging (
                guild_id INTEGER PRIMARY KEY,
                log_channel INTEGER
            )
            """,
        ],
    )

    await _execute_many(
        DB_DIR / "emoji_sync.db",
        [
            """
            CREATE TABLE IF NOT EXISTS emoji_sync_settings (
                guild_id INTEGER PRIMARY KEY,
                auto_sync INTEGER NOT NULL DEFAULT 0,
                sync_to_application INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS emoji_sync_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                status TEXT NOT NULL,
                uploaded INTEGER NOT NULL DEFAULT 0,
                skipped INTEGER NOT NULL DEFAULT 0,
                failed INTEGER NOT NULL DEFAULT 0,
                details TEXT,
                created_at TEXT NOT NULL
            )
            """,
        ],
    )

    log.info("Startup database migrations completed.")
