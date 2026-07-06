from __future__ import annotations

import logging
from functools import wraps

import discord

log = logging.getLogger(__name__)


def install_neutral_embed_policy() -> None:
    """Keep legacy embed code rendering without accent/embed colors."""
    if getattr(discord.Embed, "_axon_neutral_policy", False):
        return

    original_init = discord.Embed.__init__

    @wraps(original_init)
    def neutral_init(self, *args, **kwargs):
        kwargs.pop("color", None)
        kwargs.pop("colour", None)
        original_init(self, *args, **kwargs)
        self._colour = None

    def get_neutral_colour(self):
        return None

    def set_neutral_colour(self, value):
        self._colour = None

    discord.Embed.__init__ = neutral_init
    discord.Embed.colour = property(get_neutral_colour, set_neutral_colour)
    discord.Embed.color = discord.Embed.colour
    discord.Embed._axon_neutral_policy = True
    log.debug("Installed neutral embed color policy.")
