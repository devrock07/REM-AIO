from __future__ import annotations

import ast
import asyncio
import io
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import aiohttp
import aiosqlite
import discord
import yaml
from discord.ext import commands
from PIL import Image

from utils import emojis
from utils.components_v2 import basic_panel, button

log = logging.getLogger(__name__)

DB_PATH = "db/emoji_sync.db"
MAX_EMOJI_BYTES = 256 * 1024
SUPPORTED_ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@dataclass(slots=True)
class EmojiAsset:
    name: str
    data: bytes
    animated: bool
    source: str


@dataclass(slots=True)
class EmojiSyncResult:
    target: str
    uploaded: list[str] = field(default_factory=list)
    already_exists: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "failed" if self.failed and not self.uploaded else "completed"

    def lines(self) -> list[str]:
        return [
            f"Target: `{self.target}`",
            f"Uploaded: `{len(self.uploaded)}`",
            f"Already existed: `{len(self.already_exists)}`",
            f"Skipped: `{len(self.skipped)}`",
            f"Failed: `{len(self.failed)}`",
        ]


class EmojiSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._startup_sync_done = False
        self.config = self._load_config()

    def _load_config(self) -> dict:
        data: dict = {}
        config_path = Path("config.yml")
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as fp:
                data = yaml.safe_load(fp) or {}

        emoji_config = data.get("EMOJI_SYNC", {}) or {}
        env_sources = [
            os.getenv("EMOJI_SYNC_SOURCE_GUILD_IDS", ""),
            os.getenv("EMOJI_SYNC_SOURCE_GUILDS", ""),  # Backward-compatible alias.
        ]
        env_asset_dirs = os.getenv("EMOJI_SYNC_ASSET_DIRS", "")
        env_code_emojis = os.getenv("EMOJI_SYNC_CODE_EMOJIS")
        env_startup_sync = os.getenv("EMOJI_SYNC_STARTUP_AUTO_SYNC")

        source_ids = emoji_config.get("SOURCE_GUILD_IDS", []) or []
        for env_source in env_sources:
            if env_source:
                source_ids.extend(part.strip() for part in env_source.split(",") if part.strip())

        asset_dirs = emoji_config.get("ASSET_DIRS", []) or ["data/emojis", "assets/emojis"]
        if env_asset_dirs:
            asset_dirs.extend(part.strip() for part in env_asset_dirs.split(",") if part.strip())

        sync_code_emojis = bool(emoji_config.get("SYNC_CODE_EMOJIS", True))
        if env_code_emojis is not None:
            sync_code_emojis = env_code_emojis.lower() in {"1", "true", "yes", "on"}

        startup_auto_sync = bool(emoji_config.get("STARTUP_AUTO_SYNC", False))
        if env_startup_sync is not None:
            startup_auto_sync = env_startup_sync.lower() in {"1", "true", "yes", "on"}

        return {
            "startup_auto_sync": startup_auto_sync,
            "sync_code_emojis": sync_code_emojis,
            "source_guild_ids": [int(value) for value in source_ids if str(value).isdigit()],
            "asset_dirs": [str(value) for value in asset_dirs],
            "upload_delay": float(emoji_config.get("UPLOAD_DELAY_SECONDS", 1.5)),
            "max_bytes": int(emoji_config.get("MAX_FILE_SIZE_BYTES", MAX_EMOJI_BYTES)),
        }

    async def cog_load(self) -> None:
        await self._ensure_db()

    async def _ensure_db(self) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS emoji_sync_settings (
                    guild_id INTEGER PRIMARY KEY,
                    auto_sync INTEGER NOT NULL DEFAULT 0,
                    sync_to_application INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT
                )
                """
            )
            await db.execute(
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
                """
            )
            await db.commit()

    async def _get_settings(self, guild_id: int) -> tuple[bool, bool]:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT auto_sync, sync_to_application FROM emoji_sync_settings WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                row = await cursor.fetchone()

        if row is None:
            return False, True
        return bool(row[0]), bool(row[1])

    async def _set_settings(
        self,
        guild_id: int,
        *,
        auto_sync: Optional[bool] = None,
        sync_to_application: Optional[bool] = None,
    ) -> None:
        current_auto, current_app = await self._get_settings(guild_id)
        next_auto = current_auto if auto_sync is None else auto_sync
        next_app = current_app if sync_to_application is None else sync_to_application
        now = discord.utils.utcnow().isoformat()

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO emoji_sync_settings
                    (guild_id, auto_sync, sync_to_application, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (guild_id, int(next_auto), int(next_app), now),
            )
            await db.commit()

    async def _record_run(self, guild_id: int, result: EmojiSyncResult) -> None:
        details = {
            "target": result.target,
            "uploaded": result.uploaded,
            "already_exists": result.already_exists,
            "skipped": result.skipped,
            "failed": result.failed,
        }
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO emoji_sync_runs
                    (guild_id, status, uploaded, skipped, failed, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    result.status,
                    len(result.uploaded),
                    len(result.already_exists) + len(result.skipped),
                    len(result.failed),
                    json.dumps(details),
                    discord.utils.utcnow().isoformat(),
                ),
            )
            await db.commit()

    async def _latest_run(self, guild_id: int) -> Optional[dict]:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """
                SELECT status, uploaded, skipped, failed, created_at, details
                FROM emoji_sync_runs
                WHERE guild_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (guild_id,),
            ) as cursor:
                row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "status": row[0],
            "uploaded": row[1],
            "skipped": row[2],
            "failed": row[3],
            "created_at": row[4],
            "details": row[5],
        }

    def _sanitize_name(self, name: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9_]", "_", name).strip("_")
        if len(sanitized) < 2:
            sanitized = f"{sanitized or 'emoji'}_"
        return sanitized[:32]

    def _persist_application_emoji_ids(self, application_emojis: list[object]) -> int:
        registry_path = Path("utils/emojis.py")
        if not registry_path.exists():
            return 0

        by_name = {
            str(getattr(emoji, "name")).lower(): emoji
            for emoji in application_emojis
            if getattr(emoji, "name", None) and getattr(emoji, "id", None)
        }
        if not by_name:
            return 0

        lines = registry_path.read_text(encoding="utf-8").splitlines(keepends=True)
        updates = 0

        for index, line in enumerate(lines):
            if "CustomEmoji(" not in line or not line.lstrip()[:1].isupper():
                continue

            line_ending = "\n" if line.endswith("\n") else ""
            source = line[:-1] if line_ending else line

            try:
                node = ast.parse(source)
            except SyntaxError:
                continue

            if not node.body or not isinstance(node.body[0], ast.Assign):
                continue

            assignment = node.body[0]
            if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
                continue
            if not isinstance(assignment.value, ast.Call):
                continue
            if not isinstance(assignment.value.func, ast.Name) or assignment.value.func.id != "CustomEmoji":
                continue
            if not assignment.value.args or not isinstance(assignment.value.args[0], ast.Constant):
                continue

            emoji_name = str(assignment.value.args[0].value)
            application_emoji = by_name.get(emoji_name.lower())
            if application_emoji is None:
                continue

            next_line = (
                f"{assignment.targets[0].id} = CustomEmoji("
                f"{str(getattr(application_emoji, 'name'))!r}, "
                f"{int(getattr(application_emoji, 'id'))}, "
                f"{bool(getattr(application_emoji, 'animated', False))!r})"
                f"{line_ending}"
            )
            if next_line != line:
                lines[index] = next_line
                updates += 1

        if updates:
            registry_path.write_text("".join(lines), encoding="utf-8")
        return updates

    def _refresh_application_emoji_registry(self, application_emojis: list[object]) -> None:
        runtime_updates = emojis.apply_application_emojis(application_emojis)
        file_updates = self._persist_application_emoji_ids(application_emojis)
        if runtime_updates or file_updates:
            log.info(
                "Updated emoji registry from application emojis: runtime=%s file=%s",
                runtime_updates,
                file_updates,
            )

    async def _fetch_bytes(self, url: str) -> bytes:
        session = self.bot.session
        close_session = False
        if session is None or session.closed:
            session = aiohttp.ClientSession()
            close_session = True
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.read()
        finally:
            if close_session:
                await session.close()

    def _prepare_image(self, data: bytes, *, animated: bool) -> Optional[bytes]:
        max_bytes = self.config["max_bytes"]
        if len(data) <= max_bytes:
            return data
        if animated:
            return None

        try:
            with Image.open(io.BytesIO(data)) as image:
                image = image.convert("RGBA")
                image.thumbnail((128, 128), Image.Resampling.LANCZOS)

                for fmt, params in (
                    ("WEBP", {"quality": 90, "method": 6}),
                    ("PNG", {"optimize": True}),
                ):
                    output = io.BytesIO()
                    image.save(output, fmt, **params)
                    prepared = output.getvalue()
                    if len(prepared) <= max_bytes:
                        return prepared
        except Exception:
            log.exception("Failed to optimize emoji image")
        return None

    async def _collect_from_code_emojis(self) -> list[EmojiAsset]:
        if not self.config["sync_code_emojis"]:
            return []

        assets: list[EmojiAsset] = []
        for custom_emoji in emojis.all_custom_emojis():
            try:
                data = await self._fetch_bytes(custom_emoji.cdn_url)
                prepared = self._prepare_image(data, animated=custom_emoji.animated)
                if prepared is None:
                    log.warning(
                        "Skipped code emoji %s (%s): file exceeds Discord limit.",
                        custom_emoji.name,
                        custom_emoji.id,
                    )
                    continue

                assets.append(
                    EmojiAsset(
                        name=self._sanitize_name(custom_emoji.name),
                        data=prepared,
                        animated=custom_emoji.animated,
                        source=f"code:{custom_emoji.id}",
                    )
                )
            except aiohttp.ClientResponseError as exc:
                log.warning(
                    "Could not download code emoji %s (%s): HTTP %s",
                    custom_emoji.name,
                    custom_emoji.id,
                    exc.status,
                )
            except Exception as exc:
                log.warning("Could not download code emoji %s (%s): %s", custom_emoji.name, custom_emoji.id, exc)
        return assets

    async def _collect_from_source_guilds(self) -> list[EmojiAsset]:
        assets: list[EmojiAsset] = []
        for guild_id in self.config["source_guild_ids"]:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                log.warning("Emoji source guild %s is not available to this bot.", guild_id)
                continue

            for emoji in guild.emojis:
                try:
                    data = await self._fetch_bytes(str(emoji.url))
                    prepared = self._prepare_image(data, animated=emoji.animated)
                    if prepared is None:
                        log.warning("Skipped %s from %s: file exceeds Discord limit.", emoji.name, guild.name)
                        continue
                    assets.append(
                        EmojiAsset(
                            name=self._sanitize_name(emoji.name),
                            data=prepared,
                            animated=emoji.animated,
                            source=f"guild:{guild.id}",
                        )
                    )
                except Exception as exc:
                    log.warning("Failed to read source emoji %s from %s: %s", emoji.name, guild.id, exc)
        return assets

    async def _collect_from_asset_dirs(self) -> list[EmojiAsset]:
        assets: list[EmojiAsset] = []
        for raw_dir in self.config["asset_dirs"]:
            directory = Path(raw_dir)
            if not directory.exists() or not directory.is_dir():
                continue
            for path in directory.rglob("*"):
                if path.suffix.lower() not in SUPPORTED_ASSET_EXTENSIONS:
                    continue
                animated = path.suffix.lower() == ".gif"
                try:
                    data = path.read_bytes()
                    prepared = self._prepare_image(data, animated=animated)
                    if prepared is None:
                        log.warning("Skipped %s: file exceeds Discord emoji limit.", path)
                        continue
                    assets.append(
                        EmojiAsset(
                            name=self._sanitize_name(path.stem),
                            data=prepared,
                            animated=animated,
                            source=str(path),
                        )
                    )
                except OSError as exc:
                    log.warning("Failed to read emoji asset %s: %s", path, exc)
        return assets

    async def _collect_assets(self) -> list[EmojiAsset]:
        raw_assets = await self._collect_from_code_emojis()
        raw_assets.extend(await self._collect_from_source_guilds())
        raw_assets.extend(await self._collect_from_asset_dirs())

        assets: list[EmojiAsset] = []
        seen: set[str] = set()
        for asset in raw_assets:
            key = asset.name.lower()
            if key in seen:
                log.info("Skipped duplicate source emoji name: %s", asset.name)
                continue
            seen.add(key)
            assets.append(asset)
        return assets

    def _has_guild_slots(self, guild: discord.Guild, *, animated: bool) -> bool:
        limit = getattr(guild, "emoji_limit", 50)
        count = sum(1 for emoji in guild.emojis if emoji.animated is animated)
        return count < limit

    async def _sync_to_guild(self, guild: discord.Guild, assets: list[EmojiAsset]) -> EmojiSyncResult:
        result = EmojiSyncResult(target=f"server:{guild.id}")
        existing_names = {emoji.name.lower() for emoji in guild.emojis}
        me = guild.me or guild.get_member(self.bot.user.id)
        perms = me.guild_permissions if me else None

        can_create = bool(
            perms
            and (
                getattr(perms, "create_expressions", False)
                or getattr(perms, "manage_expressions", False)
                or getattr(perms, "manage_emojis_and_stickers", False)
                or getattr(perms, "administrator", False)
            )
        )
        if not can_create:
            result.failed.append("Missing Create Expressions or Manage Expressions permission.")
            return result

        for asset in assets:
            key = asset.name.lower()
            if key in existing_names:
                result.already_exists.append(asset.name)
                continue
            if not self._has_guild_slots(guild, animated=asset.animated):
                result.skipped.append(f"{asset.name}: no {'animated' if asset.animated else 'static'} emoji slots")
                continue

            try:
                created = await guild.create_custom_emoji(
                    name=asset.name,
                    image=asset.data,
                    reason="Axon emoji sync",
                )
                existing_names.add(created.name.lower())
                result.uploaded.append(created.name)
                log.info("Uploaded guild emoji %s to %s", created.name, guild.id)
                await asyncio.sleep(self.config["upload_delay"])
            except discord.Forbidden:
                result.failed.append(f"{asset.name}: missing permissions")
                break
            except discord.HTTPException as exc:
                result.failed.append(f"{asset.name}: HTTP {exc.status}")
                log.warning("Guild emoji upload failed for %s: %s", asset.name, exc)
                await asyncio.sleep(self.config["upload_delay"])
            except Exception as exc:
                result.failed.append(f"{asset.name}: {exc}")
                log.exception("Guild emoji upload failed for %s", asset.name)
        return result

    async def _sync_to_application(self, guild_id: int, assets: list[EmojiAsset]) -> EmojiSyncResult:
        result = EmojiSyncResult(target="application")
        try:
            existing = list(await self.bot.fetch_application_emojis())
        except Exception as exc:
            result.failed.append(f"Could not fetch application emojis: {exc}")
            return result

        self._refresh_application_emoji_registry(existing)
        existing_names = {emoji.name.lower() for emoji in existing}
        if len(existing) >= 2000:
            result.failed.append("Application emoji limit reached.")
            return result

        for asset in assets:
            key = asset.name.lower()
            if key in existing_names:
                result.already_exists.append(asset.name)
                continue
            if len(existing_names) >= 2000:
                result.skipped.append(f"{asset.name}: application emoji limit reached")
                continue

            try:
                created = await self.bot.create_application_emoji(name=asset.name, image=asset.data)
                existing.append(created)
                existing_names.add(created.name.lower())
                result.uploaded.append(created.name)
                log.info("Uploaded application emoji %s for guild %s", created.name, guild_id)
                await asyncio.sleep(self.config["upload_delay"])
            except discord.HTTPException as exc:
                result.failed.append(f"{asset.name}: HTTP {exc.status}")
                log.warning("Application emoji upload failed for %s: %s", asset.name, exc)
                await asyncio.sleep(self.config["upload_delay"])
            except Exception as exc:
                result.failed.append(f"{asset.name}: {exc}")
                log.exception("Application emoji upload failed for %s", asset.name)

        self._refresh_application_emoji_registry(existing)
        return result

    async def run_sync(
        self,
        guild: Optional[discord.Guild] = None,
        *,
        target: Literal["guild", "application"],
    ) -> EmojiSyncResult:
        guild_id = guild.id if guild is not None else 0
        assets = await self._collect_assets()
        if not assets:
            result = EmojiSyncResult(target=target)
            result.skipped.append("No code emoji IDs, source guild emojis, or local emoji assets were found.")
            await self._record_run(guild_id, result)
            return result

        if target == "application":
            result = await self._sync_to_application(guild_id, assets)
        else:
            if guild is None:
                result = EmojiSyncResult(target="server")
                result.failed.append("Server emoji sync requires a target server.")
                await self._record_run(guild_id, result)
                return result
            result = await self._sync_to_guild(guild, assets)

        await self._record_run(guild_id, result)
        return result

    def _settings_panel(self, guild: discord.Guild, auto_sync: bool, app_sync: bool, latest: Optional[dict]):
        last_line = "Last run: `Never`"
        if latest:
            last_line = (
                f"Last run: `{latest['status']}` at `{latest['created_at']}` "
                f"(uploaded {latest['uploaded']}, skipped {latest['skipped']}, failed {latest['failed']})"
            )

        lines = [
            f"Server: `{guild.name}`",
            f"Startup auto-sync: `{'Enabled' if auto_sync else 'Disabled'}`",
            f"Application emoji target: `{'Enabled' if app_sync else 'Disabled'}`",
            f"Code emoji IDs configured: `{len(emojis.all_custom_emojis()) if self.config['sync_code_emojis'] else 0}`",
            f"Source guilds configured: `{len(self.config['source_guild_ids'])}`",
            f"Asset directories configured: `{len(self.config['asset_dirs'])}`",
            last_line,
        ]
        actions = [
            button("Sync App", f"emoji_sync:sync:application:{guild.id}", style=discord.ButtonStyle.primary),
            button("Sync Server", f"emoji_sync:sync:guild:{guild.id}", style=discord.ButtonStyle.secondary),
            button(
                "Disable Auto" if auto_sync else "Enable Auto",
                f"emoji_sync:auto:{0 if auto_sync else 1}:{guild.id}",
                style=discord.ButtonStyle.secondary,
            ),
            button(
                "Disable App Target" if app_sync else "Enable App Target",
                f"emoji_sync:app:{0 if app_sync else 1}:{guild.id}",
                style=discord.ButtonStyle.secondary,
            ),
            button("Status", f"emoji_sync:status:guild:{guild.id}", style=discord.ButtonStyle.secondary),
        ]
        return basic_panel("Emoji Sync", lines, actions=actions, timeout=None)

    async def _send_result(self, destination, title: str, result: EmojiSyncResult) -> None:
        extra: list[str] = []
        if result.uploaded:
            extra.append("Uploaded names: " + ", ".join(f"`{name}`" for name in result.uploaded[:15]))
        if result.failed:
            extra.append("Failures: " + "; ".join(result.failed[:8]))
        if result.skipped:
            extra.append("Skipped: " + "; ".join(result.skipped[:8]))

        view = basic_panel(title, result.lines() + extra, timeout=180)
        await destination.send(view=view)

    @commands.Cog.listener()
    async def on_ready(self):
        if self._startup_sync_done:
            return
        self._startup_sync_done = True
        await self.bot.wait_until_ready()

        if not self.config["startup_auto_sync"]:
            return

        try:
            result = await self.run_sync(target="application")
            log.info(
                "Startup application emoji sync complete: uploaded=%s already=%s skipped=%s failed=%s",
                len(result.uploaded),
                len(result.already_exists),
                len(result.skipped),
                len(result.failed),
            )
        except Exception:
            log.exception("Startup application emoji sync failed")

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT guild_id, sync_to_application FROM emoji_sync_settings WHERE auto_sync = 1"
            ) as cursor:
                rows = await cursor.fetchall()

        for guild_id, app_target in rows:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                continue
            try:
                if app_target:
                    await self.run_sync(guild, target="application")
                else:
                    await self.run_sync(guild, target="guild")
            except Exception:
                log.exception("Startup emoji sync failed for guild %s", guild_id)

    @commands.hybrid_group(
        name="emojisync",
        aliases=["emoji-sync", "emojis"],
        invoke_without_command=True,
        help="Manage automatic emoji synchronization.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def emojisync(self, ctx: commands.Context):
        auto_sync, app_sync = await self._get_settings(ctx.guild.id)
        latest = await self._latest_run(ctx.guild.id)
        await ctx.send(view=self._settings_panel(ctx.guild, auto_sync, app_sync, latest))

    @emojisync.command(name="run", help="Run emoji sync now.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def emojisync_run(
        self,
        ctx: commands.Context,
        target: Literal["guild", "application"] = "application",
    ):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        result = await self.run_sync(ctx.guild, target=target)
        await self._send_result(ctx, "Emoji Sync Complete", result)

    @emojisync.command(name="auto", help="Enable or disable startup emoji sync for this server.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def emojisync_auto(self, ctx: commands.Context, enabled: bool):
        await self._set_settings(ctx.guild.id, auto_sync=enabled)
        auto_sync, app_sync = await self._get_settings(ctx.guild.id)
        latest = await self._latest_run(ctx.guild.id)
        await ctx.send(view=self._settings_panel(ctx.guild, auto_sync, app_sync, latest))

    @emojisync.command(name="application", help="Enable or disable application emoji sync as part of auto-sync.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def emojisync_application(self, ctx: commands.Context, enabled: bool):
        await self._set_settings(ctx.guild.id, sync_to_application=enabled)
        auto_sync, app_sync = await self._get_settings(ctx.guild.id)
        latest = await self._latest_run(ctx.guild.id)
        await ctx.send(view=self._settings_panel(ctx.guild, auto_sync, app_sync, latest))

    @emojisync.command(name="status", help="Show emoji sync status and configured sources.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def emojisync_status(self, ctx: commands.Context):
        auto_sync, app_sync = await self._get_settings(ctx.guild.id)
        latest = await self._latest_run(ctx.guild.id)
        await ctx.send(view=self._settings_panel(ctx.guild, auto_sync, app_sync, latest))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        data = interaction.data or {}
        custom_id = data.get("custom_id")
        if not isinstance(custom_id, str) or not custom_id.startswith("emoji_sync:"):
            return

        if interaction.guild is None:
            await interaction.response.send_message("Emoji sync can only be managed in a server.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only administrators can manage emoji sync.", ephemeral=True)
            return

        parts = custom_id.split(":")
        if len(parts) != 4 or int(parts[3]) != interaction.guild.id:
            await interaction.response.send_message("This control is not for this server.", ephemeral=True)
            return

        action, value = parts[1], parts[2]

        if action == "sync":
            target = "application" if value == "application" else "guild"
            await interaction.response.defer(ephemeral=True, thinking=True)
            result = await self.run_sync(interaction.guild, target=target)
            await interaction.followup.send(view=basic_panel("Emoji Sync Complete", result.lines(), timeout=180), ephemeral=True)
            return

        if action == "auto":
            await self._set_settings(interaction.guild.id, auto_sync=value == "1")
        elif action == "app":
            await self._set_settings(interaction.guild.id, sync_to_application=value == "1")
        elif action == "status":
            auto_sync, app_sync = await self._get_settings(interaction.guild.id)
            latest = await self._latest_run(interaction.guild.id)
            await interaction.response.send_message(
                view=self._settings_panel(interaction.guild, auto_sync, app_sync, latest),
                ephemeral=True,
            )
            return

        auto_sync, app_sync = await self._get_settings(interaction.guild.id)
        latest = await self._latest_run(interaction.guild.id)
        await interaction.response.edit_message(view=self._settings_panel(interaction.guild, auto_sync, app_sync, latest))
