from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_PROJECT_ROOT / ".env")

__all__ = [
    "TOKEN",
    "PREFIX",
    "NAME",
    "BotName",
    "server",
    "serverLink",
    "ch",
    "OWNER_IDS",
    "BYPASS_IDS",
    "COMMAND_LOG_IGNORE_IDS",
    "GUILD_JOIN_LOG_CHANNEL_ID",
    "GUILD_LEAVE_LOG_CHANNEL_ID",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "GIPHY_TOKEN",
    "GOOGLE_API_KEY",
    "GOOGLE_SEARCH_ENGINE_ID",
    "RAPIDAPI_KEY",
    "RAPIDAPI_HOST",
    "OPENWEATHER_API_KEY",
    "PEXELS_API_KEY",
    "MAPQUEST_API_KEY",
    "OPENAI_API_KEY",
    "LAVALINK_ENABLED",
    "LAVALINK_URI",
    "LAVALINK_PASSWORD",
    "ENABLE_KEEP_ALIVE",
    "COMMAND_LOG_WEBHOOK_URL",
    "LOG_LEVEL",
    "PORT",
    "env_bool",
    "env_str",
    "csv_ints",
]


def env_str(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def csv_ints(name: str, default: list[int] | None = None) -> list[int]:
    raw = os.environ.get(name, "")
    if not raw.strip():
        return list(default or [])

    values: list[int] = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            values.append(int(part))
    return values or list(default or [])


def _csv_int_or_none(name: str) -> int | None:
    raw = env_str(name)
    return int(raw) if raw.isdigit() else None


TOKEN = env_str("TOKEN")
PREFIX = env_str("PREFIX", ">") or ">"
NAME = env_str("BOT_NAME", "REM ALL IN ONE BOT")
server = env_str("SUPPORT_SERVER", "https://discord.gg/stVsvE9rhT")
ch = env_str("SUPPORT_CHANNEL", "https://discord.com/channels/699587669059174461/1271825678710476911")

OWNER_IDS = set(csv_ints("OWNER_IDS"))
_bypass = csv_ints("BYPASS_IDS")
BYPASS_IDS = set(_bypass) if _bypass else set(OWNER_IDS)
_ignore = csv_ints("COMMAND_LOG_IGNORE_IDS")
COMMAND_LOG_IGNORE_IDS = set(_ignore) if _ignore else set(OWNER_IDS)

GUILD_JOIN_LOG_CHANNEL_ID = _csv_int_or_none("GUILD_JOIN_LOG_CHANNEL_ID")
GUILD_LEAVE_LOG_CHANNEL_ID = _csv_int_or_none("GUILD_LEAVE_LOG_CHANNEL_ID")

SPOTIFY_CLIENT_ID = env_str("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = env_str("SPOTIFY_CLIENT_SECRET")
GIPHY_TOKEN = env_str("GIPHY_TOKEN")
GOOGLE_API_KEY = env_str("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = env_str("GOOGLE_SEARCH_ENGINE_ID")
RAPIDAPI_KEY = env_str("RAPIDAPI_KEY")
RAPIDAPI_HOST = env_str("RAPIDAPI_HOST", "truth-dare.p.rapidapi.com")
OPENWEATHER_API_KEY = env_str("OPENWEATHER_API_KEY")
PEXELS_API_KEY = env_str("PEXELS_API_KEY")
MAPQUEST_API_KEY = env_str("MAPQUEST_API_KEY")
OPENAI_API_KEY = env_str("OPENAI_API_KEY") or env_str("AI_API_KEY")

LAVALINK_ENABLED = env_bool("LAVALINK_ENABLED", True)
LAVALINK_URI = env_str("LAVALINK_URI")
LAVALINK_PASSWORD = env_str("LAVALINK_PASSWORD")

COMMAND_LOG_WEBHOOK_URL = env_str("COMMAND_LOG_WEBHOOK_URL")
ENABLE_KEEP_ALIVE = env_bool("ENABLE_KEEP_ALIVE", True)
LOG_LEVEL = env_str("LOG_LEVEL", "INFO").upper()
PORT = int(env_str("PORT", "8080") or "8080")

BotName = NAME
serverLink = server