import json
from quart import Quart, request
import aiohttp
import aiosqlite
import datetime
import pytz

app = Quart(__name__)

BOT_TOKEN = "YOUR-BOT-TOKEN"

@app.before_serving
async def setup_database():
    async with aiosqlite.connect("votes.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                user_id TEXT PRIMARY KEY,
                total_votes INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                last_vote_time TEXT
            )
        """)
        await db.commit()

@app.route('/')
async def index():
    return {'webhook': 'olympus'}

async def get_user_avatar(user_id):
    url = f"https://discord.com/api/v10/users/{user_id}"
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                user_data = await response.json()
                avatar = user_data.get("avatar")
                if avatar:
                    return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png"
                else:
                    default_avatar_id = int(user_id) % 5
                    return f"https://cdn.discordapp.com/embed/avatars/{default_avatar_id}.png"
            else:
                return None

@app.route('/topgg/', methods=['POST'])
async def topgg():
    authorization = request.headers.get('Authorization')
    webhook = 'YOUR-VOTE-POSTER-CHANNEL-WEBHOOK'

    if authorization != 'YOUR-TOPGG-AUTHORIZATION':
        return {'error': '401 Unauthorized'}, 401

    data = json.loads(await request.data)
    user_id = data['user']
    avatar_url = await get_user_avatar(user_id)

    if not avatar_url:
        return {'error': 'Failed to fetch avatar'}, 500

    current_time = datetime.datetime.now()

    async with aiosqlite.connect("votes.db") as db:
        cursor = await db.execute(
            "SELECT total_votes, streak, last_vote_time FROM votes WHERE user_id = ?",
            (user_id,)
        )
        user_data = await cursor.fetchone()
        await cursor.close()

        if user_data:
            total_votes, streak, last_vote_time = user_data
            last_vote_time = datetime.datetime.fromisoformat(last_vote_time)
            time_difference = (current_time - last_vote_time).total_seconds()

            if time_difference <= 43200:  
                streak += 1
            else:
                streak = 1
        else:
            total_votes = 0
            streak = 1

        total_votes += 1
        await db.execute(
            """
            INSERT INTO votes (user_id, total_votes, streak, last_vote_time)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_votes = excluded.total_votes,
                streak = excluded.streak,
                last_vote_time = excluded.last_vote_time
            """,
            (user_id, total_votes, streak, current_time.isoformat())
        )
        await db.commit()

    timestamp = (current_time + datetime.timedelta(hours=12)).timestamp()

    india_tz = pytz.timezone('Asia/Kolkata')
    
    footer_time_utc = current_time.replace(tzinfo=pytz.utc)
    footer_time_india = footer_time_utc.astimezone(india_tz)
    footer_time = footer_time_india.strftime('%d/%m/%Y %I:%M %p')

    webhook_data = {
        "username": "Olympus",
        "content": f"<@{user_id}> voted for <@1144179659735572640>!",
        "embeds": [
            {
                "description": "**[Voted Olympus](https://top.gg/bot/1144179659735572640)**\n💖 Thank you for voting for Olympus on Top.gg, your support means everything to us!\n",
                "fields": [
                    {"name": "⏰ Time left to vote again:", "value": f"<t:{int(timestamp)}:R>\n‎ \n", "inline": True},
                    {"name": "📊 Total votes:", "value": f"{total_votes}", "inline": True},
                    {"name": "🏆 Current Streak:", "value": f"{streak}", "inline": True},
                ],
                "footer": {
                    "text": f"Voter ID: {user_id} | Olympus Development™ | {footer_time}",
                    "icon_url": "https://cdn.discordapp.com/icons/699587669059174461/f689b4366447d5a23eda8d0ec749c1ba.png?size=1024"
                },
                "thumbnail": {
                    "url": avatar_url
                },
                "color": 0xff0000
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        await session.post(webhook, json=webhook_data)

    return {"message": "Vote registered successfully!"}
