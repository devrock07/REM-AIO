# REM ALL IN ONE BOT

REM ALL IN ONE BOT is a modified version of Axon X, built as an all-in-one Discord bot with moderation, automod, antinuke, music, utility, games, welcome, logging, giveaway, ticket, and server-management features.

## Requirements

- Python 3.11 or newer
- A Discord bot token
- A Lavalink node for music commands

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file from `.env.example` and fill in your values:

```env
TOKEN=your_discord_bot_token
COMMAND_LOG_WEBHOOK_URL=
LOG_LEVEL=INFO
ENABLE_KEEP_ALIVE=true
PORT=8080

LAVALINK_ENABLED=true
LAVALINK_IDENTIFIER=main
LAVALINK_URI=http://host:port
LAVALINK_PASSWORD=your_lavalink_password
LAVALINK_PRECHECK=true
```

3. Update owner IDs and other bot constants in `utils/config.py`.

4. Start the bot:

```bash
python rem.py
```

## Configuration Notes

- Keep secrets in `.env`; do not commit tokens, passwords, database files, or generated logs.
- Default prefix and guild config are managed by the bot configuration utilities.
- Music commands require a working Lavalink server.
- Runtime SQLite databases are created locally as the bot runs.

## Credits

REM ALL IN ONE BOT is a modified version of Axon X. Original project lineage includes Axon X and Olympus bot components.
