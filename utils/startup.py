from __future__ import annotations

import logging

from utils.config import (
    LAVALINK_ENABLED,
    LAVALINK_PASSWORD,
    LAVALINK_URI,
    OWNER_IDS,
    PREFIX,
    TOKEN,
)

log = logging.getLogger("rem.startup")


class StartupError(RuntimeError):
    pass


def validate_startup_config() -> list[str]:
    """Validate required config and return non-fatal warnings."""
    warnings: list[str] = []

    if not TOKEN:
        raise StartupError("TOKEN is not set. Add it to .env or your process environment.")

    if not OWNER_IDS:
        warnings.append("OWNER_IDS is empty — no bot owners are configured.")

    if len(PREFIX) > 10:
        warnings.append("PREFIX is longer than 10 characters — per-server prefix changes are capped at 10.")

    if LAVALINK_ENABLED and (not LAVALINK_URI or not LAVALINK_PASSWORD):
        warnings.append(
            "LAVALINK_ENABLED is true but LAVALINK_URI or LAVALINK_PASSWORD is missing — music will be disabled."
        )

    for warning in warnings:
        log.warning(warning)

    return warnings