<p align="center">
  <img src="remaio.png" alt="REM ALL IN ONE BOT" width="100%">
</p>

# REM ALL IN ONE BOT

REM ALL IN ONE BOT is a modified version of Axon X. It is an all-in-one Discord bot focused on clean panels, moderation, server security, music, tickets, giveaways, utilities, games, welcome systems, logging, and server management.

## Features

- Components V2 styled help, utility, and music panels
- Lavalink/Wavelink music playback with player controls
- Moderation commands for bans, kicks, timeouts, warnings, locks, hides, roles, purges, and snipes
- Antinuke protection for dangerous server changes
- Automod protection for spam, caps, links, invites, mass mentions, and emoji spam
- Ticket panels, giveaways, logging, welcome/greet, autorole, autoreact, and custom roles
- Utility commands such as stats, botinfo, profile, invite, serverinfo, userinfo, ping, uptime, AFK, translate, QR, and emoji tools
- Games and fun commands including chess, RPS, tic-tac-toe, Wordle, 2048, blackjack, slots, and more
- Owner/staff controls for no-prefix, global actions, reloads, and bot administration

## Requirements

- Python 3.11 or newer
- A Discord bot application and token
- Message Content intent enabled in the Discord Developer Portal
- Server Members intent enabled if you use moderation, welcome, autorole, AFK mention tracking, or antinuke features
- A Lavalink node for music commands

## Installation

Clone or open the project folder, then install the Python dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
copy .env.example .env
```

Fill `.env` with your real values. Keep this file private.

```env
TOKEN=your_discord_bot_token
BOT_NAME=REM ALL IN ONE BOT
OWNER_IDS=123456789012345678
BYPASS_IDS=123456789012345678
COMMAND_LOG_IGNORE_IDS=123456789012345678

LAVALINK_ENABLED=true
LAVALINK_IDENTIFIER=main
LAVALINK_URI=http://127.0.0.1:2333
LAVALINK_PASSWORD=youshallnotpass
LAVALINK_SECURE=false
```

Start the bot:

```bash
python rem.py
```

## Environment

Important `.env` values:

| Key | Purpose |
| --- | --- |
| `TOKEN` | Discord bot token. Required. |
| `BOT_NAME` | Display name used by bot panels and config helpers. |
| `OWNER_IDS` | Comma-separated Discord user IDs with owner-level access. |
| `BYPASS_IDS` | Comma-separated user IDs allowed through production security checks. Usually owners. |
| `COMMAND_LOG_IGNORE_IDS` | Users ignored by command logging. |
| `SUPPORT_SERVER` | Invite/support link used in panels. |
| `COMMAND_LOG_WEBHOOK_URL` | Optional webhook for command logs. |
| `LAVALINK_URI` | Lavalink node URL, for example `http://host:2333`. |
| `LAVALINK_PASSWORD` | Lavalink node password. |
| `OPENAI_API_KEY` | Optional AI/chat key for AI features. |

Use `.env.example` as the full reference. Do not commit `.env`, tokens, passwords, local databases, logs, or generated runtime files.

## Permissions

For normal operation, invite the bot with these permissions:

- Administrator, or a carefully configured role with the permissions below
- Manage Server, Manage Roles, Manage Channels, Manage Messages
- Ban Members, Kick Members, Moderate Members
- View Audit Log
- Send Messages, Embed Links, Attach Files, Use External Emojis
- Connect, Speak, Use Voice Activity for music

Sensitive setup commands are restricted to owners, bypass users, server owners, administrators, or members with the correct Discord permissions depending on the command. Ticket panels, giveaways, automod, security setup, antinuke, emergency, and similar server-control commands should not be available to normal members.

## Music

Music requires Lavalink. Configure the node in `.env`:

```env
LAVALINK_ENABLED=true
LAVALINK_IDENTIFIER=main
LAVALINK_URI=http://your-lavalink-host:2333
LAVALINK_PASSWORD=your_lavalink_password
LAVALINK_PRECHECK=true
```

If the music panel or controls do not update after code changes, fully restart the running `python rem.py` process. Hot-saving files will not update an already running bot process.

## Project Layout

```text
rem.py                 Bot entrypoint
cogs/commands/         Main command cogs
cogs/moderation/       Moderation commands
cogs/antinuke/         Antinuke listeners
cogs/automod/          Automod listeners
cogs/events/           Bot event listeners
core/                  Bot class and startup helpers
utils/                 Config, checks, UI helpers, and shared utilities
data/                  Runtime assets and local bot data
db/                    Runtime database helpers/state
```

## Development Checks

Run a quick syntax check after edits:

```bash
python -m compileall rem.py cogs utils core
```

Check the current Git changes:

```bash
git status --short
```

## Security Notes

- Regenerate the bot token immediately if it is ever posted in chat, screenshots, logs, or commits.
- Keep `.env` local only.
- Do not commit `.db`, `.sqlite`, log, cache, or generated media files.
- Keep owner and bypass IDs limited to trusted users.
- Restart the bot after permission, security, music, or environment changes.

## Credits

REM ALL IN ONE BOT is a modified version of Axon X. Original project lineage includes Axon X and Olympus bot components.
