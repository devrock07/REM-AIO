from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from discord.ext import commands

from utils.cache import TTLCache
from utils.config import BYPASS_IDS, OWNER_IDS, PREFIX
from utils.database import connect

if TYPE_CHECKING:
    import discord
    from core.Context import Context

DEFAULT_PREFIX = PREFIX

# Tuned for a large command surface: comfortable normal use, firm anti-spam.
RATE_BURST_LIMIT = 10
RATE_BURST_WINDOW = 5.0
RATE_SUSTAINED_LIMIT = 60
RATE_SUSTAINED_WINDOW = 60.0
RATE_LIMIT_NOTIFY_COOLDOWN = 12.0

_UI_INTERACTION_PREFIXES = (
    "help:v2:",
    "help:list:",
    "paginator:",
)


@dataclass(frozen=True, slots=True)
class AccessDecision:
    allowed: bool
    reason: str = ""


class CommandRateLimiter:
    """Burst + sustained per-user command rate limiting."""

    __slots__ = (
        "burst_limit",
        "burst_window",
        "sustained_limit",
        "sustained_window",
        "_events",
    )

    def __init__(
        self,
        *,
        burst_limit: int = RATE_BURST_LIMIT,
        burst_window: float = RATE_BURST_WINDOW,
        sustained_limit: int = RATE_SUSTAINED_LIMIT,
        sustained_window: float = RATE_SUSTAINED_WINDOW,
    ) -> None:
        self.burst_limit = burst_limit
        self.burst_window = burst_window
        self.sustained_limit = sustained_limit
        self.sustained_window = sustained_window
        self._events: dict[int, deque[float]] = defaultdict(deque)

    def _prune(self, bucket: deque[float], now: float, window: float) -> None:
        while bucket and now - bucket[0] > window:
            bucket.popleft()

    def check(self, user_id: int) -> tuple[bool, float]:
        now = time.monotonic()
        bucket = self._events[user_id]
        self._prune(bucket, now, self.sustained_window)

        recent_burst = [stamp for stamp in bucket if now - stamp <= self.burst_window]
        if len(recent_burst) >= self.burst_limit:
            retry = self.burst_window - (now - recent_burst[0])
            return False, max(retry, 0.1)

        if len(bucket) >= self.sustained_limit:
            retry = self.sustained_window - (now - bucket[0])
            return False, max(retry, 0.1)

        bucket.append(now)
        return True, 0.0


class SecurityGate:
    """Cached security lookups shared across commands and listeners."""

    def __init__(self) -> None:
        self._prefix_cache = TTLCache[str](ttl=120.0)
        self._np_cache = TTLCache[bool](ttl=300.0)
        self._blacklist_cache = TTLCache[AccessDecision](ttl=45.0)
        self._ignore_cache = TTLCache[dict[str, set[str]]](ttl=30.0)
        self._topcheck_cache = TTLCache[bool](ttl=60.0)
        self.rate_limiter = CommandRateLimiter()
        self._trusted_users = set(OWNER_IDS) | set(BYPASS_IDS)
        self._rate_limit_notify: dict[int, float] = {}

    def is_trusted(self, user_id: int) -> bool:
        return user_id in self._trusted_users

    async def get_prefix(self, guild_id: int) -> str:
        key = f"prefix:{guild_id}"
        cached = await self._prefix_cache.get(key)
        if cached is not None:
            return cached

        async with connect("prefix.db") as db:
            async with db.execute(
                "SELECT prefix FROM prefixes WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                row = await cursor.fetchone()

        prefix = row[0] if row else DEFAULT_PREFIX
        if not row:
            async with connect("prefix.db") as db:
                await db.execute(
                    "INSERT OR REPLACE INTO prefixes (guild_id, prefix) VALUES (?, ?)",
                    (guild_id, prefix),
                )
                await db.commit()

        await self._prefix_cache.set(key, prefix)
        return prefix

    async def invalidate_prefix(self, guild_id: int) -> None:
        await self._prefix_cache.invalidate(f"prefix:{guild_id}")

    async def has_no_prefix(self, user_id: int) -> bool:
        key = f"np:{user_id}"
        cached = await self._np_cache.get(key)
        if cached is not None:
            return cached

        async with connect("np.db") as db:
            async with db.execute("SELECT 1 FROM np WHERE id = ?", (user_id,)) as cursor:
                enabled = await cursor.fetchone() is not None

        await self._np_cache.set(key, enabled)
        return enabled

    async def invalidate_no_prefix(self, user_id: int) -> None:
        await self._np_cache.invalidate(f"np:{user_id}")

    async def check_blacklist(self, user_id: int, guild_id: int | None) -> AccessDecision:
        key = f"block:{user_id}:{guild_id or 0}"
        cached = await self._blacklist_cache.get(key)
        if cached is not None:
            return cached

        async with connect("block.db") as db:
            async with db.execute(
                "SELECT 1 FROM user_blacklist WHERE user_id = ?",
                (str(user_id),),
            ) as cursor:
                if await cursor.fetchone():
                    decision = AccessDecision(False, "user_blacklisted")
                    await self._blacklist_cache.set(key, decision)
                    return decision

            if guild_id is not None:
                async with db.execute(
                    "SELECT 1 FROM guild_blacklist WHERE guild_id = ?",
                    (str(guild_id),),
                ) as cursor:
                    if await cursor.fetchone():
                        decision = AccessDecision(False, "guild_blacklisted")
                        await self._blacklist_cache.set(key, decision)
                        return decision

        decision = AccessDecision(True)
        await self._blacklist_cache.set(key, decision)
        return decision

    async def get_ignore_data(self, guild_id: int) -> dict[str, set[str]]:
        key = f"ignore:{guild_id}"
        cached = await self._ignore_cache.get(key)
        if cached is not None:
            return cached

        data: dict[str, set[str]] = {
            "channel": set(),
            "user": set(),
            "command": set(),
            "bypassuser": set(),
        }

        async with connect("ignore.db") as db:
            async with db.execute(
                "SELECT channel_id FROM ignored_channels WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                data["channel"] = {str(row[0]) for row in await cursor.fetchall()}

            async with db.execute(
                "SELECT user_id FROM ignored_users WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                data["user"] = {str(row[0]) for row in await cursor.fetchall()}

            async with db.execute(
                "SELECT command_name FROM ignored_commands WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                data["command"] = {row[0].strip().lower() for row in await cursor.fetchall()}

            async with db.execute(
                "SELECT user_id FROM bypassed_users WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                data["bypassuser"] = {str(row[0]) for row in await cursor.fetchall()}

        await self._ignore_cache.set(key, data)
        return data

    async def invalidate_ignore(self, guild_id: int) -> None:
        await self._ignore_cache.invalidate(f"ignore:{guild_id}")

    async def check_ignore(self, ctx: Context) -> AccessDecision:
        if ctx.guild is None or ctx.command is None:
            return AccessDecision(True)

        data = await self.get_ignore_data(ctx.guild.id)
        author_id = str(ctx.author.id)
        channel_id = str(ctx.channel.id)

        if author_id in data["bypassuser"]:
            return AccessDecision(True)
        if channel_id in data["channel"]:
            return AccessDecision(False, "channel_ignored")
        if author_id in data["user"]:
            return AccessDecision(False, "user_ignored")

        command_name = ctx.command.name.strip().lower()
        aliases = {alias.strip().lower() for alias in ctx.command.aliases}
        ignored = data["command"]
        if command_name in ignored or aliases & ignored:
            return AccessDecision(False, "command_ignored")

        return AccessDecision(True)

    async def is_topcheck_enabled(self, guild_id: int) -> bool:
        key = f"topcheck:{guild_id}"
        cached = await self._topcheck_cache.get(key)
        if cached is not None:
            return cached

        async with connect("topcheck.db") as db:
            async with db.execute(
                "SELECT enabled FROM topcheck WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                row = await cursor.fetchone()

        enabled = row is not None and row[0] == 1
        await self._topcheck_cache.set(key, enabled)
        return enabled

    async def invalidate_topcheck(self, guild_id: int) -> None:
        await self._topcheck_cache.invalidate(f"topcheck:{guild_id}")

    async def invalidate_blacklist(self, user_id: int | None = None, guild_id: int | None = None) -> None:
        if user_id is not None:
            await self._blacklist_cache.invalidate(f"block:{user_id}:{guild_id or 0}")
        if guild_id is not None:
            await self._blacklist_cache.invalidate(f"block:0:{guild_id}")
        if user_id is None and guild_id is None:
            await self._blacklist_cache.clear()

    def check_rate_limit(self, user_id: int) -> tuple[bool, float]:
        if user_id in self._trusted_users:
            return True, 0.0
        return self.rate_limiter.check(user_id)

    def should_notify_rate_limit(self, user_id: int) -> bool:
        """Only surface one rate-limit panel per user per cooldown window."""
        now = time.monotonic()
        last = self._rate_limit_notify.get(user_id, 0.0)
        if now - last < RATE_LIMIT_NOTIFY_COOLDOWN:
            return False
        self._rate_limit_notify[user_id] = now
        return True

    @staticmethod
    def _is_ui_interaction(interaction: discord.Interaction) -> bool:
        data = getattr(interaction, "data", None)
        custom_id = getattr(data, "custom_id", None) if data is not None else None
        if not custom_id:
            return False
        return custom_id.startswith(_UI_INTERACTION_PREFIXES)

    async def run_command_gate(self, ctx: Context) -> AccessDecision:
        if self.is_trusted(ctx.author.id):
            return AccessDecision(True)

        if ctx.command:
            root = ctx.command.root_parent or ctx.command
            if root.name in {"help", "h"}:
                return AccessDecision(True)
            if getattr(ctx, "invoked_with", None) in {"help", "h"}:
                return AccessDecision(True)

        if ctx.guild is not None:
            blocked = await self.check_blacklist(ctx.author.id, ctx.guild.id)
            if not blocked.allowed:
                return blocked

        ignored = await self.check_ignore(ctx)
        if not ignored.allowed:
            return ignored

        ok, retry = self.check_rate_limit(ctx.author.id)
        if not ok:
            return AccessDecision(False, f"rate_limit:{retry:.1f}")

        return AccessDecision(True)

    async def run_interaction_gate(self, interaction: discord.Interaction) -> AccessDecision:
        user = interaction.user
        if self.is_trusted(user.id):
            return AccessDecision(True)

        if self._is_ui_interaction(interaction):
            return AccessDecision(True)

        guild_id = interaction.guild_id
        blocked = await self.check_blacklist(user.id, guild_id)
        if not blocked.allowed:
            return blocked

        ok, retry = self.check_rate_limit(user.id)
        if not ok:
            return AccessDecision(False, f"rate_limit:{retry:.1f}")

        return AccessDecision(True)


_security_gate = SecurityGate()


def get_security_gate() -> SecurityGate:
    return _security_gate