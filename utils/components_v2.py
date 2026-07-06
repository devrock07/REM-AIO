from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

import discord

IS_COMPONENTS_V2 = 1 << 15


def text(content: str) -> discord.ui.TextDisplay:
    return discord.ui.TextDisplay(content)


def separator(*, visible: bool = True) -> discord.ui.Separator:
    return discord.ui.Separator(visible=visible)


def action_row(*items: discord.ui.Item) -> discord.ui.ActionRow:
    return discord.ui.ActionRow(*items)


def button(
    label: str,
    custom_id: str,
    *,
    style: discord.ButtonStyle = discord.ButtonStyle.secondary,
    disabled: bool = False,
) -> discord.ui.Button:
    return discord.ui.Button(
        label=label,
        custom_id=custom_id,
        style=style,
        disabled=disabled,
    )


def link_button(label: str, url: str) -> discord.ui.Button:
    return discord.ui.Button(label=label, url=url, style=discord.ButtonStyle.link)


def container(*children: discord.ui.Item) -> discord.ui.Container:
    return discord.ui.Container(*children)


def layout_view(*children: discord.ui.Item, timeout: Optional[float] = 180) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView(timeout=timeout)
    for child in children:
        view.add_item(child)
    return view


def basic_panel(
    title: str,
    lines: Iterable[str],
    *,
    actions: Iterable[discord.ui.Button] = (),
    timeout: Optional[float] = 180,
) -> discord.ui.LayoutView:
    components: list[discord.ui.Item] = [text(f"## {title}")]
    body = "\n".join(line for line in lines if line)
    if body:
        components.extend([separator(), text(body)])

    action_items = list(actions)
    if action_items:
        components.append(separator())
        for index in range(0, len(action_items), 5):
            components.append(action_row(*action_items[index : index + 5]))

    return layout_view(container(*components), timeout=timeout)


def success_panel(
    description: str,
    *,
    title: str = "",
    fields: Iterable[tuple[str, str]] = (),
    footer: str = "",
    actions: Iterable[discord.ui.Button] = (),
    timeout: Optional[float] = 180,
) -> discord.ui.LayoutView:
    return response_panel(description, title=title, fields=fields, footer=footer, actions=actions, timeout=timeout)


def error_panel(
    description: str,
    *,
    title: str = "",
    fields: Iterable[tuple[str, str]] = (),
    footer: str = "",
    actions: Iterable[discord.ui.Button] = (),
    timeout: Optional[float] = 180,
) -> discord.ui.LayoutView:
    return response_panel(description, title=title, fields=fields, footer=footer, actions=actions, timeout=timeout)


def info_panel(
    description: str,
    *,
    title: str = "",
    fields: Iterable[tuple[str, str]] = (),
    footer: str = "",
    actions: Iterable[discord.ui.Button] = (),
    timeout: Optional[float] = 180,
) -> discord.ui.LayoutView:
    return response_panel(description, title=title, fields=fields, footer=footer, actions=actions, timeout=timeout)


def warning_panel(
    description: str,
    *,
    title: str = "",
    fields: Iterable[tuple[str, str]] = (),
    footer: str = "",
    actions: Iterable[discord.ui.Button] = (),
    timeout: Optional[float] = 180,
) -> discord.ui.LayoutView:
    return response_panel(description, title=title, fields=fields, footer=footer, actions=actions, timeout=timeout)


def response_panel(
    description: str,
    *,
    title: str = "",
    fields: Iterable[tuple[str, str]] = (),
    footer: str = "",
    actions: Iterable[discord.ui.Button] = (),
    timeout: Optional[float] = 180,
) -> discord.ui.LayoutView:
    parts: list[discord.ui.Item] = []
    if title:
        parts.append(text(f"### {title}"))
        parts.append(separator(visible=False))
    if description:
        parts.append(text(description))
    for name, value in fields:
        parts.append(separator(visible=False))
        parts.append(text(f"**{name}**\n{value}"))
    if footer:
        parts.append(separator())
        parts.append(text(f"-# {footer}"))

    action_items = list(actions)
    if action_items:
        parts.append(separator())
        for index in range(0, len(action_items), 5):
            parts.append(action_row(*action_items[index : index + 5]))

    return layout_view(container(*parts), timeout=timeout)
