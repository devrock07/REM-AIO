"""Kawaii CV2 card builders for REM music commands."""
from __future__ import annotations

from typing import Any, Optional, Sequence

import discord

from utils.components_v2 import container, layout_view, separator, text
from utils.cv2_compat import panel_with_actions

FOOTER_BRAND = "REM ALL IN ONE BOT"

_HEADERS = {
    "now_playing": "♡ ⋆｡˚ **Now Playing** ˚｡⋆ ♡",
    "player": "✧･ﾟ: *Music Player* :･ﾟ✧",
    "search": "✧･ﾟ: *Search Results* :･ﾟ✧",
    "platform": "♡ **Choose a Platform** ♡",
    "queue": "♡ ⋆｡˚ **Song Queue** ˚｡⋆ ♡",
    "queue_ended": "♡ **Queue Finished** ♡",
    "inactive": "♡ **Idle Timeout** ♡",
    "added": "♡ **Added to Queue** ♡",
    "lavalink": "♡ **Music Offline** ♡",
}

_TOAST_TITLES = {
    "success": "Done",
    "error": "Error",
    "warning": "Notice",
    "info": "Music",
    "added": "Queued",
}

_SOURCE_BADGES = {
    "Spotify": "🎧 Spotify",
    "YouTube": "▶️ YouTube",
    "SoundCloud": "☁️ SoundCloud",
    "JioSaavn": "🎶 JioSaavn",
    "Unknown Source": "🎵 Music",
}


def format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_duration_ms(ms: int | float) -> str:
    return format_duration((ms or 0) / 1000)


def kawaii_progress_bar(completed: float, total: float, *, length: int = 12) -> str:
    if total <= 0:
        return "♡ " + "─" * length + " ♡"
    ratio = max(0.0, min(1.0, completed / total))
    filled = int(length * ratio)
    if filled >= length:
        bar = "━" * length
    else:
        bar = "━" * filled + "○" + "─" * max(0, length - filled - 1)
    return f"♡ {bar} ♡"


def source_badge(source_name: str) -> str:
    return _SOURCE_BADGES.get(source_name, _SOURCE_BADGES["Unknown Source"])


def kawaii_footer(*, requested_by: str = "", autoplay: bool = False, extra: str = "") -> str:
    parts: list[str] = []
    if requested_by:
        suffix = " (autoplay mode~)" if autoplay else ""
        parts.append(f"♡ requested by **{requested_by}**{suffix}")
    if extra:
        parts.append(extra)
    parts.append(FOOTER_BRAND)
    return " · ".join(parts)


def _track_title_line(track: Any) -> str:
    title = getattr(track, "title", "Unknown track") or "Unknown track"
    uri = getattr(track, "uri", None)
    safe = str(title).replace("[", "\\[").replace("]", "\\]")
    return f"**[{safe}]({uri})**" if uri else f"**{safe}**"


def _artwork_url(track: Any) -> Optional[str]:
    artwork = getattr(track, "artwork", None)
    return str(artwork) if artwork else None


def now_playing_embed(
    track: Any,
    *,
    position: float = 0,
    queue_length: int = 0,
    source_name: str = "Unknown Source",
    source_link: str = "",
    requested_by: str = "",
    autoplay: bool = False,
) -> discord.Embed:
    length = (getattr(track, "length", 0) or 0) / 1000
    progress = kawaii_progress_bar(position, length)
    pos_str = format_duration(position)
    len_str = format_duration(length)

    embed = discord.Embed(
        title=_HEADERS["now_playing"],
        description=(
            f"{_track_title_line(track)}\n"
            f"> ✿ **Artist** · `{getattr(track, 'author', 'Unknown')}`\n"
            f"> ✿ **Source** · {source_badge(source_name)}\n"
            f"> ✿ **Progress** · `{pos_str}` {progress} `{len_str}`\n"
            f"> ✿ **Up next** · `{queue_length}` track{'s' if queue_length != 1 else ''} in queue"
        ),
        color=0xFFB7C5,
    )
    if source_link:
        embed.add_field(name="Listen", value=source_link, inline=False)
    artwork = _artwork_url(track)
    if artwork:
        embed.set_thumbnail(url=artwork)
    embed.set_footer(text=kawaii_footer(requested_by=requested_by, autoplay=autoplay))
    return embed


def player_embed(
    track: Any,
    *,
    source_name: str = "Unknown Source",
    source_link: str = "",
    requested_by: str = "",
    autoplay: bool = False,
    queue_length: int = 0,
    volume: int = 100,
) -> discord.Embed:
    length = format_duration_ms(getattr(track, "length", 0) or 0)
    embed = discord.Embed(
        title=_HEADERS["player"],
        description=(
            f"{_track_title_line(track)}\n"
            f"> ✿ **Artist** · `{getattr(track, 'author', 'Unknown')}`\n"
            f"> ✿ **Duration** · `{length}`\n"
            f"> ✿ **Source** · {source_badge(source_name)}\n"
            f"> ✿ **Queue** · `{queue_length}` upcoming · **Volume** · `{volume}%`"
        ),
        color=0xFFC0CB,
    )
    if source_link:
        embed.add_field(name="Listen", value=source_link, inline=False)
    artwork = _artwork_url(track)
    if artwork:
        embed.set_thumbnail(url=artwork)
    embed.set_footer(text=kawaii_footer(requested_by=requested_by, autoplay=autoplay))
    return embed


def search_results_embed(
    query: str,
    source: str,
    tracks: Sequence[Any],
) -> discord.Embed:
    platform = source.replace("search", "").upper() or "MUSIC"
    lines = []
    for index, track in enumerate(tracks, start=1):
        duration = format_duration_ms(getattr(track, "length", 0) or 0)
        lines.append(
            f"`{index}.` {_track_title_line(track)}\n"
            f"> ✿ `{getattr(track, 'author', 'Unknown')}` · `{duration}`"
        )
    embed = discord.Embed(
        title=_HEADERS["search"],
        description=(
            f"*Results for* **{query}** *on* **{platform}**\n"
            f"♡ tap a number below to play\n\n" + "\n\n".join(lines)
        ),
        color=0xFFD1DC,
    )
    embed.set_footer(text="♡ pick a track below · " + FOOTER_BRAND)
    return embed


def platform_select_embed(query: str) -> discord.Embed:
    return discord.Embed(
        title=_HEADERS["platform"],
        description=(
            f"*Searching for* **{query}**\n\n"
            "✿ **YouTube** — videos & covers\n"
            "✿ **JioSaavn** — regional hits\n"
            "✿ **SoundCloud** — indie & remixes\n\n"
            "♡ pick where to search"
        ),
        color=0xFFB6C1,
    )


def queue_embed(
    entries: Sequence[str],
    *,
    page: int = 0,
    total_pages: int = 1,
    now_playing: Optional[Any] = None,
) -> discord.Embed:
    body = "\n".join(entries) if entries else "*nothing queued yet~*"
    description = f"♡ **Page {page + 1}/{total_pages}**\n\n{body}"
    if now_playing is not None:
        description = (
            f"**Now spinning~**\n{_track_title_line(now_playing)}\n\n"
            f"**Coming up next**\n{body}"
        )
    embed = discord.Embed(
        title=_HEADERS["queue"],
        description=description,
        color=0xF8C8DC,
    )
    embed.set_footer(text="♡ upcoming tracks · " + FOOTER_BRAND)
    return embed


def queue_entry_line(index: int, track: Any) -> str:
    duration = format_duration_ms(getattr(track, "length", 0) or 0)
    return (
        f"`{index:02d}.` {_track_title_line(track)}\n"
        f"> ✿ `{getattr(track, 'author', 'Unknown')}` · `{duration}`"
    )


def music_toast(
    message: str,
    *,
    title: str = "",
    tone: str = "info",
) -> discord.ui.LayoutView:
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "♡",
        "added": "♡",
    }
    icon = icons.get(tone, "♡")
    header = title or _TOAST_TITLES.get(tone, "Music")
    return layout_view(
        container(
            text(f"## {icon} {header}"),
            separator(visible=False),
            text(message),
            separator(),
            text(f"-# {FOOTER_BRAND}"),
        ),
        timeout=90,
    )


def guard_no_voice() -> discord.ui.LayoutView:
    return music_toast("Join a voice channel first.", tone="warning")


def guard_same_channel() -> discord.ui.LayoutView:
    return music_toast("You need to be in my voice channel.", tone="warning")


def guard_not_playing() -> discord.ui.LayoutView:
    return music_toast("Nothing is playing right now.", tone="warning")


def guard_not_connected() -> discord.ui.LayoutView:
    return music_toast("I'm not connected to a voice channel.", tone="warning")


def guard_no_results() -> discord.ui.LayoutView:
    return music_toast("No results found — try a different search.", tone="error")


def guard_empty_queue() -> discord.ui.LayoutView:
    return music_toast("The queue is empty. Use `>play` to add songs.", tone="warning")


def queue_ended_embed() -> discord.Embed:
    return discord.Embed(
        title=_HEADERS["queue_ended"],
        description=(
            "All the songs finished playing~ I'm heading out of voice now.\n\n"
            "♡ thanks for vibing with REM!"
        ),
        color=0xFFB7C5,
    )


def inactivity_embed() -> discord.Embed:
    return discord.Embed(
        title=_HEADERS["inactive"],
        description=(
            "I was alone in voice for 2 minutes with no one around~\n"
            "Disconnected to save resources. Join me again anytime!"
        ),
        color=0xFFC0CB,
    )


def lavalink_offline_embed(warning_emoji: str) -> discord.Embed:
    return discord.Embed(
        title=_HEADERS["lavalink"],
        description=(
            f"{warning_emoji} Music can't connect to Lavalink right now.\n"
            "Set `LAVALINK_URI` and `LAVALINK_PASSWORD` in `.env`, then restart the bot."
        ),
        color=0xFF8FAB,
    )


def player_layout_view(
    embed: discord.Embed,
    controls: discord.ui.View,
    *,
    timeout: Optional[float] = None,
) -> discord.ui.LayoutView:
    return panel_with_actions(embed, controls, timeout=timeout)


def kawaii_queue_page_source(
    entries: Sequence[str],
    *,
    per_page: int = 5,
    now_playing: Any = None,
    requested_by: str = "",
):
    """Build a kawaii queue paginator page source for discord-ext-menus."""
    from discord.ext import menus

    class _KawaiiQueuePageSource(menus.ListPageSource):
        def __init__(self) -> None:
            super().__init__(list(entries), per_page=per_page)
            self._now_playing = now_playing
            self._requested_by = requested_by

        async def format_page(self, menu, page_entries) -> discord.Embed:
            maximum = self.get_max_pages() or 1
            embed = queue_embed(
                list(page_entries),
                page=menu.current_page,
                total_pages=maximum,
                now_playing=self._now_playing if menu.current_page == 0 else None,
            )
            if self._requested_by:
                footer = f"♡ requested by **{self._requested_by}** · {FOOTER_BRAND}"
                if maximum > 1:
                    footer = f"♡ page {menu.current_page + 1}/{maximum} · requested by **{self._requested_by}** · {FOOTER_BRAND}"
                embed.set_footer(text=footer)
            return embed

    return _KawaiiQueuePageSource()