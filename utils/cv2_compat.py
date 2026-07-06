"""
cv2_compat.py — Drop-in Panel class that renders discord.Embed-style content
as a Components V2 LayoutView (discord.ui.Container).

Usage:
    panel = Panel(title="Success", description="Role added!", color=0x00ff00)
    panel.add_field(name="Member", value="`devii`")
    panel.set_footer(text="Requested by devii")
    await panel.send(ctx)         # ctx.send(view=...)
    await panel.reply(ctx)        # ctx.reply(view=..., mention_author=False)

    # Or one-liner:
    await cv2_send(ctx, title="Done", description="Action completed.")
"""
from __future__ import annotations

from typing import Optional, Any
import discord

__all__ = ("Panel", "cv2_send")


class Panel:
    """Embed-compatible wrapper that outputs a Components V2 LayoutView."""

    def __init__(
        self,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Any = None,
    ) -> None:
        self.title = title
        self.description = description
        self.color = color  # kept for API compat, not used visually
        self._author_name: Optional[str] = None
        self._footer_text: Optional[str] = None
        self._fields: list[tuple[str, str, bool]] = []

    # ── Embed-compatible setters ───────────────────────────────────────────

    def set_author(self, *, name: str, icon_url: Optional[str] = None) -> "Panel":
        self._author_name = name
        return self

    def set_footer(self, *, text: str, icon_url: Optional[str] = None) -> "Panel":
        self._footer_text = text
        return self

    def add_field(self, *, name: str, value: str, inline: bool = False) -> "Panel":
        self._fields.append((name, value, inline))
        return self

    def set_thumbnail(self, *, url: str) -> "Panel":
        return self  # not supported in CV2 containers — silently ignored

    def set_image(self, *, url: str) -> "Panel":
        return self  # not supported in CV2 containers — silently ignored

    # ── Build ──────────────────────────────────────────────────────────────

    def to_view(self, timeout: Optional[float] = None) -> discord.ui.LayoutView:
        children: list[discord.ui.Item] = []

        # Author line (shown before title if present)
        if self._author_name:
            children.append(discord.ui.TextDisplay(f"> {self._author_name}"))

        # Title
        if self.title:
            children.append(discord.ui.TextDisplay(f"## {self.title}"))

        # Separator after header block
        if self._author_name or self.title:
            children.append(discord.ui.Separator(visible=False))

        # Description
        if self.description:
            children.append(discord.ui.TextDisplay(self.description))

        # Fields
        if self._fields:
            if self.description or self.title or self._author_name:
                children.append(discord.ui.Separator(visible=True))
            for name, value, _ in self._fields:
                children.append(discord.ui.TextDisplay(f"**{name}**\n{value}"))

        # Footer
        if self._footer_text:
            children.append(discord.ui.Separator(visible=True))
            children.append(discord.ui.TextDisplay(f"-# {self._footer_text}"))

        container = discord.ui.Container(*children)
        view = discord.ui.LayoutView(timeout=timeout)
        view.add_item(container)
        return view

    # ── Send helpers ───────────────────────────────────────────────────────

    async def send(self, ctx, content: Optional[str] = None, **kwargs) -> Optional[discord.Message]:
        kwargs.pop("embed", None)  # drop any stray embed kwarg
        return await ctx.send(content=content, view=self.to_view(), **kwargs)

    async def reply(
        self,
        ctx,
        content: Optional[str] = None,
        mention_author: bool = False,
        **kwargs,
    ) -> Optional[discord.Message]:
        kwargs.pop("embed", None)
        return await ctx.reply(
            content=content,
            view=self.to_view(),
            mention_author=mention_author,
            **kwargs,
        )

    async def edit(self, message: discord.Message, content: Optional[str] = None, **kwargs) -> discord.Message:
        kwargs.pop("embed", None)
        return await message.edit(content=content, view=self.to_view(), **kwargs)


# ── One-liner helper ───────────────────────────────────────────────────────────

async def cv2_send(
    ctx,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: Any = None,
    fields: Optional[list[tuple[str, str]]] = None,
    footer: Optional[str] = None,
    author: Optional[str] = None,
    mention_author: bool = False,
    reply: bool = False,
    content: Optional[str] = None,
    **kwargs,
) -> Optional[discord.Message]:
    """
    Quick one-liner CV2 sender.

    fields = [(name, value), ...]
    """
    panel = Panel(title=title, description=description, color=color)
    if author:
        panel.set_author(name=author)
    if footer:
        panel.set_footer(text=footer)
    for name, value in (fields or []):
        panel.add_field(name=name, value=value)

    if reply:
        return await panel.reply(ctx, content=content, mention_author=mention_author, **kwargs)
    return await panel.send(ctx, content=content, **kwargs)
