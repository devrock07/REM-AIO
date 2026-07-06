from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from utils import emojis
from utils.components_v2 import action_row, separator, text


MAX_PAGE_CHARS = 3600


class HelpDropdown(discord.ui.Select):
    def __init__(self, ctx: commands.Context, options: list[discord.SelectOption]):
        super().__init__(
            placeholder="Choose a Category for Help",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"help:v2:select:{ctx.author.id}",
        )
        self.invoker = ctx.author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.invoker:
            await interaction.response.send_message(
                "You must run this command to interact with it.",
                ephemeral=True,
            )
            return

        view: HelpView = self.view  # type: ignore[assignment]
        index = view.find_index_from_select(self.values[0])
        await view.set_page(index, interaction)


class HelpButton(discord.ui.Button):
    def __init__(
        self,
        *,
        invoker: discord.abc.User,
        action: str,
        emoji: str,
        disabled: bool = False,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
    ):
        super().__init__(
            emoji=emoji,
            style=style,
            custom_id=f"help:v2:{action}:{invoker.id}",
            disabled=disabled,
        )
        self.invoker = invoker
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.invoker:
            await interaction.response.send_message(
                "You must run this command to interact with it.",
                ephemeral=True,
            )
            return

        view: HelpView = self.view  # type: ignore[assignment]

        if self.action == "home":
            await view.set_page(0, interaction)

        elif self.action == "prev":
            await view.set_page(view.index - 1, interaction)

        elif self.action == "delete":
            await interaction.response.defer()
            if interaction.message:
                await interaction.message.delete()

        elif self.action == "next":
            await view.set_page(view.index + 1, interaction)

        elif self.action == "last":
            await view.set_page(view.total_pages - 1, interaction)


class HelpView(discord.ui.LayoutView):
    def __init__(
        self,
        mapping: dict,
        ctx: commands.Context,
        homeembed: Optional[discord.Embed] = None,
        ui: int = 2,
        *,
        prefix: Optional[str] = None,
        total_commands: Optional[int] = None,
    ):
        super().__init__(timeout=None)

        self.mapping = mapping
        self.ctx = ctx
        self.prefix = prefix or getattr(ctx, "prefix", ">") or ">"
        self.total_commands = total_commands or len(set(ctx.bot.walk_commands()))
        self.index = 0

        self.pages, self.options = self._build_pages()
        self.total_pages = len(self.pages)

        self._render()

    def get_cogs(self):
        return list(self.mapping.keys())

    def find_index_from_select(self, value: str) -> int:
        for index, option in enumerate(self.options):
            if option.value == value:
                return index
        return 0

    def _bot_logo_url(self) -> Optional[str]:
        bot_user = self.ctx.bot.user

        if not bot_user:
            return None

        if bot_user.display_avatar:
            return bot_user.display_avatar.url

        if bot_user.avatar:
            return bot_user.avatar.url

        return None

    def _home_header(self) -> str:
        return "\n".join(
            [
                f"{emojis.BLUEDOT} **Server Prefix:** `{self.prefix}`",
                f"{emojis.BLUEDOT} **Total Commands:** `{self.total_commands}`",
                f"{emojis.BLUEDOT} Type `{self.prefix}antinuke enable` to get started",
            ]
        )

    def _home_modules(self) -> str:
        module_lines = [
            f"{emojis.VOICE_003466} Voice",
            f"{emojis.GAMES} Games",
            f"{emojis.GREET} Welcomer",
            f"{emojis.AUTOREACT} Autoreact & Responder",
            f"{emojis.AUTOROLE} Autorole & Invc",
            f"{emojis.EXTRA} Fun & AI Image Gen",
            f"{emojis.IGNORE} Ignore Channels",
            f"{emojis.LOGGING} Advance Logging",
            f"{emojis.INVITETRACKER} Invite Tracker",
        ]

        return "\n".join(
            [
                f"{emojis.MODULE} **Modules**",
                *module_lines,
            ]
        )

    def _home_features(self) -> str:
        feature_lines = [
            f"{emojis.SECURITY} Security",
            f"{emojis.BOTS} Automoderation",
            f"{emojis.UTILITY} Utility",
            f"{emojis.MUSIC} Music",
            f"{emojis.MODERATION} Moderation",
            f"{emojis.CUSTOMROLE} Customrole",
            f"{emojis.GIVEAWAY_644980} Giveaway",
            f"{emojis.TICKET} Ticket",
            f"{emojis.VANITYROLES} Vanityroles",
        ]

        return "\n".join(
            [
                f"{emojis.FILDER} **My Features**",
                *feature_lines,
            ]
        )

    def _build_home_page(self) -> str:
        return "\n\n".join(
            [
                self._home_header(),
                self._home_modules(),
                self._home_features(),
            ]
        )

    def _home_header_component(self):
        logo_url = self._bot_logo_url()

        Section = getattr(discord.ui, "Section", None)
        Thumbnail = getattr(discord.ui, "Thumbnail", None)

        if not logo_url or Section is None or Thumbnail is None:
            return text(self._home_header())

        try:
            return Section(
                text(self._home_header()),
                accessory=Thumbnail(logo_url),
            )
        except Exception:
            return text(self._home_header())

    def _build_command_page(self, cog) -> str:
        emoji, label, description = cog.help_custom()

        all_cmds = []

        for cmd in cog.get_commands():
            if cmd.hidden:
                continue

            if (
                isinstance(cmd, commands.Group)
                and cmd.name.startswith("__")
                and not list(cmd.walk_commands())
                and cmd.help
            ):
                doc_list = cmd.help.strip()

                lines = [
                    f"{emoji} {label}",
                    "",
                    f"**{label}**",
                    doc_list,
                ]

                page = "\n".join(lines).strip()

                if len(page) > MAX_PAGE_CHARS:
                    page = page[: MAX_PAGE_CHARS - 20].rstrip() + "\n`...`"

                return page

            all_cmds.append(cmd)

            if isinstance(cmd, commands.Group):
                all_cmds.extend(sub for sub in cmd.walk_commands() if not sub.hidden)

        lines = [
            f"{emoji} {label}",
            "",
            f"**{label}**",
        ]

        if not all_cmds:
            lines.append("*No commands available.*")
        else:
            cmd_tags = " , ".join(f"`{cmd.name}`" for cmd in all_cmds)
            lines.append(cmd_tags)

        page = "\n".join(lines).strip()

        if len(page) > MAX_PAGE_CHARS:
            page = page[: MAX_PAGE_CHARS - 20].rstrip() + "\n`...`"

        return page

    def _build_pages(self) -> tuple[list[str], list[discord.SelectOption]]:
        pages = [self._build_home_page()]

        options = [
            discord.SelectOption(
                label="Home",
                value="__home__",
                emoji=str(emojis.HOME),
                description="Main help panel",
            )
        ]

        for cog in self.get_cogs():
            if "help_custom" not in dir(cog):
                continue

            emoji, label, description = cog.help_custom()

            pages.append(self._build_command_page(cog))

            options.append(
                discord.SelectOption(
                    label=label[:100],
                    value=label[:100],
                    emoji=str(emoji),
                    description=(description or "")[:100],
                )
            )

        return pages, options[:25]

    def _footer(self) -> str:
        return (
            f"- Help page {self.index + 1}/{self.total_pages} "
            f"| Requested by: {self.ctx.author.display_name}"
        )

    def _nav_buttons(self) -> list[HelpButton]:
        prev_emoji = getattr(emojis, "PREVIOUS", emojis.NEXT)

        return [
            HelpButton(
                invoker=self.ctx.author,
                action="home",
                emoji=str(emojis.REWIND1),
                disabled=self.index == 0,
            ),
            HelpButton(
                invoker=self.ctx.author,
                action="prev",
                emoji=str(prev_emoji),
                disabled=self.index == 0,
            ),
            HelpButton(
                invoker=self.ctx.author,
                action="delete",
                emoji=str(emojis.DELETE),
                style=discord.ButtonStyle.danger,
            ),
            HelpButton(
                invoker=self.ctx.author,
                action="next",
                emoji=str(emojis.ICONS_NEXT),
                disabled=self.index >= self.total_pages - 1,
            ),
            HelpButton(
                invoker=self.ctx.author,
                action="last",
                emoji=str(emojis.FORWARD),
                disabled=self.index >= self.total_pages - 1,
            ),
        ]

    def _render_home(self) -> None:
        self.add_item(
            discord.ui.Container(
                self._home_header_component(),
                separator(),
                text(self._home_modules()),
                separator(),
                text(self._home_features()),
                separator(),
                text(self._footer()),
                separator(),
                action_row(*self._nav_buttons()),
                action_row(HelpDropdown(self.ctx, self.options)),
            )
        )

    def _render_command_page(self) -> None:
        self.add_item(
            discord.ui.Container(
                text(self.pages[self.index]),
                separator(),
                text(self._footer()),
                separator(),
                action_row(*self._nav_buttons()),
                action_row(HelpDropdown(self.ctx, self.options)),
            )
        )

    def _render(self) -> None:
        self.clear_items()

        if self.index == 0:
            self._render_home()
        else:
            self._render_command_page()

    async def set_page(self, page: int, interaction: discord.Interaction):
        self.index = max(0, min(page, self.total_pages - 1))
        self._render()

        if interaction.response.is_done():
            await interaction.edit_original_response(view=self)
        else:
            await interaction.response.edit_message(view=self)


View = HelpView
