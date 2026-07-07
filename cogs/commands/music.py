from utils import emojis

import json
import os
import random
import discord
from discord.ext import commands, tasks
import datetime
from discord.ui import Button, View
import wavelink
from wavelink.enums import TrackSource
from utils import Paginator
from core import Cog, Rem, Context

import aiohttp
import asyncio
from utils.Tools import *
from utils.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from utils.cv2_compat import embed_to_view
from utils.music_panel import (
    guard_empty_queue,
    guard_no_results,
    guard_no_voice,
    guard_not_connected,
    guard_not_playing,
    guard_same_channel,
    inactivity_embed,
    kawaii_queue_page_source,
    lavalink_offline_embed,
    music_toast,
    now_playing_embed,
    platform_select_embed,
    player_embed,
    player_layout_view,
    queue_ended_embed,
    queue_entry_line,
    search_results_embed,
)
track_histories = {}
import base64
import re
import logging
from urllib.parse import urljoin

import yaml

log = logging.getLogger(__name__)
BOT_DISPLAY_NAME = "REM ALL IN ONE BOT"

SPOTIFY_TRACK_REGEX = r"https?://open\.spotify\.com/track/([a-zA-Z0-9]+)"
SPOTIFY_PLAYLIST_REGEX = r"https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)"
SPOTIFY_ALBUM_REGEX = r"https?://open\.spotify\.com/album/([a-zA-Z0-9]+)"

class SpotifyAPI:
    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    async def get_token(self):
        auth_url = "https://accounts.spotify.com/api/token"
        auth_value = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode('utf-8')).decode('utf-8')
        headers = {"Authorization": f"Basic {auth_value}"}
        data = {"grant_type": "client_credentials"}
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, headers=headers, data=data) as response:
                text = await response.text()
                if response.status != 200:
                    raise Exception(f"Failed to fetch token: {response.status}, response: {text}")
                self.token = (await response.json()).get("access_token")

    async def get(self, endpoint, params=None):
        retries = 2
        for attempt in range(retries):
            if not self.token or attempt > 0:
                await self.get_token()

            url = f"{self.BASE_URL}/{endpoint}"
            headers = {"Authorization": f"Bearer {self.token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 401 and attempt < retries - 1:
                        continue
                    elif response.status != 200:
                        raise Exception(f"Failed to fetch data from Spotify: {response.status}")
                    return await response.json()
        raise Exception("Exceeded max retries to fetch Spotify data")

    
    async def get_track(self, track_id):
        return await self.get(f"tracks/{track_id}")

    async def get_playlist(self, playlist_id):
        return await self.get(f"playlists/{playlist_id}")

_spotify_api: SpotifyAPI | None = None


def get_spotify_api() -> SpotifyAPI | None:
    global _spotify_api
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    if _spotify_api is None:
        _spotify_api = SpotifyAPI(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
    return _spotify_api

class PlatformSelectView(View):
    def __init__(self, ctx, query):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.query = query

        platforms = [
            ("♡ YouTube", "ytsearch", discord.ButtonStyle.danger),
            ("♡ JioSaavn", "jssearch", discord.ButtonStyle.success),
            ("♡ SoundCloud", "scsearch", discord.ButtonStyle.secondary),
        ]

        for name, source, style in platforms:
            button = Button(label=name, style=style)
            button.callback = self.create_callback(source)
            self.add_item(button)

    def create_callback(self, source):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("Only the command author can select a platform.", ephemeral=True)
                return

            await interaction.response.send_message("✧ searching… one moment!", ephemeral=True)
            await self.perform_search(source)
            await interaction.message.delete()
        return callback

    async def perform_search(self, source):
        if self.ctx.cog and not await self.ctx.cog.ensure_lavalink(self.ctx):
            return

        results = await wavelink.Playable.search(self.query, source=source)
        if not results:
            return await self.ctx.send(view=guard_no_results())

        top_results = results[:5]
        embed = search_results_embed(self.query, source, top_results)
        await self.ctx.send(view=embed_to_view(embed, view=SearchResultView(self.ctx, top_results)))

    

class SearchResultView(View):
    def __init__(self, ctx, results):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.results = results

        for i in range(min(5, len(results))):
            button = Button(label=f"♡ {i + 1}", style=discord.ButtonStyle.primary)
            button.callback = self.create_callback(i)
            self.add_item(button)

    def create_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("Only the command author can select a track.", ephemeral=True)
                return

            track = self.results[index]
            vc = self.ctx.voice_client or await self.ctx.author.voice.channel.connect(cls=wavelink.Player)
            vc.ctx = self.ctx


            if not vc.playing:
                await vc.play(track)
                await interaction.response.send_message(f"♡ Now playing **{track.title}**", ephemeral=True)
                await self.ctx.cog.display_player_embed(vc, track, self.ctx)

            else:
                await vc.queue.put_wait(track)
                await interaction.response.send_message(f"♡ Added **{track.title}** to the queue", ephemeral=True)

        return callback



class MusicControlView(View):
    def __init__(self, player, ctx):
        super().__init__(timeout=None)
        self.player = player
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.ctx.voice_client or not self.player.playing:
            await interaction.response.send_message("I'm not currently playing this anymore.", ephemeral=True)
            return False
        if interaction.user in self.ctx.voice_client.channel.members:
            return True
        await interaction.response.send_message(
            "♡ Join my voice channel to use the player controls.",
            ephemeral=True,
        )
        return False

    @discord.ui.button(emoji=f"{emojis.VOICE}", style=discord.ButtonStyle.secondary)
    async def autoplay_button(self, interaction: discord.Interaction, button: Button):
        self.player.autoplay = (
            wavelink.AutoPlayMode.enabled if self.player.autoplay != wavelink.AutoPlayMode.enabled else wavelink.AutoPlayMode.disabled
        )
        await interaction.response.send_message(f"Autoplay {'enabled' if self.player.autoplay == wavelink.AutoPlayMode.enabled else 'disabled'} by **{interaction.user.display_name}**.")


    @discord.ui.button(emoji=f"{emojis.REWIND1}", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        guild_id = interaction.guild.id

        if guild_id in track_histories and len(track_histories[guild_id]) > 1:
            track_histories[guild_id].pop()
            previous_track = track_histories[guild_id][-1] 

            player = self.player 
            vc = self.ctx.voice_client

            if player.playing:
                await player.stop()

            await player.play(previous_track)
            await interaction.response.send_message(f"Playing previous track: `{previous_track.title}`.")
        else:
            await interaction.response.send_message("No previous track available.", ephemeral=True)

    @discord.ui.button(emoji=f"{emojis.MUSICSTOP_ICONS}", style=discord.ButtonStyle.success)
    async def pause_button(self, interaction: discord.Interaction, button: Button):
        if self.player.paused:
            await self.player.pause(False)

            await self.player.channel.edit(status=f"{emojis.MUSIC} Playing: {self.player.current.title}")
            button.emoji = f"{emojis.MUSICSTOP_ICONS}" 
            await interaction.response.edit_message(view=button.view)

        elif self.player.playing:
            await self.player.pause(True)
            await self.player.channel.edit(status=f"{emojis.ICONS_PAUSE}  Paused: {self.player.current.title}")
            button.emoji = f"{emojis.ICONS_PAUSE}"
            await interaction.response.edit_message(view=button.view)


    @discord.ui.button(emoji=f"{emojis.SKIP}", style=discord.ButtonStyle.secondary)
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        if self.player.autoplay == wavelink.AutoPlayMode.enabled:
            await self.player.stop()
            return await interaction.response.send_message(f"Skipped song by **{interaction.user.display_name}**.")
            #await self.player.play(await self.player.queue.get_next_track())

        if self.player and self.player.playing and not self.player.queue.is_empty:
            await self.player.stop()
            await interaction.response.send_message(f"Skipped song by **{interaction.user.display_name}**.")
        else:
            await interaction.response.send_message("No song in queue to skip.", ephemeral=True)


    @discord.ui.button(emoji=f"{emojis.ICONLOAD}", style=discord.ButtonStyle.secondary)
    async def loop_button(self, interaction: discord.Interaction, button: Button):
        self.player.queue.mode = wavelink.QueueMode.loop if self.player.queue.mode != wavelink.QueueMode.loop else wavelink.QueueMode.normal
        await interaction.response.send_message(f"Loop {'enabled' if self.player.queue.mode == wavelink.QueueMode.loop else 'disabled'} by **{interaction.user.display_name}**.")


    @discord.ui.button(emoji=f"{emojis.SHUFFLE}", style=discord.ButtonStyle.secondary)
    async def shuffle_button(self, interaction: discord.Interaction, button: Button):
        if self.player.queue:
            random.shuffle(self.player.queue)
            await interaction.response.send_message(f"Queue shuffled by **{interaction.user.display_name}**.")
        else:
            await interaction.response.send_message("Queue is empty.", ephemeral=True)


    @discord.ui.button(emoji=f"{emojis.REWIND1}", style=discord.ButtonStyle.secondary)
    async def rewind_button(self, interaction: discord.Interaction, button: Button):
        if self.player.playing:
            new_position = max(self.player.position - 10000, 0)
            await self.player.seek(new_position)
            await interaction.response.send_message("Rewinded 10 seconds.", ephemeral=True)
        else:
            await interaction.response.send_message("No track is currently playing.", ephemeral=True)

    @discord.ui.button(emoji=f"{emojis.MUSICSTOP_ICONS}", style=discord.ButtonStyle.secondary)
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        if self.player:
            voice_channel = self.player.channel
            if voice_channel:
                await voice_channel.edit(status=None)

            await self.player.disconnect()
            await interaction.response.send_message(f"Stopped and disconnected by **{interaction.user.display_name}**.")
        else:
            await interaction.response.send_message("Not connected.", ephemeral=True)

    @discord.ui.button(emoji=f"{emojis.FORWARD}", style=discord.ButtonStyle.secondary)
    async def forward_button(self, interaction: discord.Interaction, button: Button):
        if self.player.playing:
            new_position = min(self.player.position + 10000, self.player.current.length)
            await self.player.seek(new_position)
            await interaction.response.send_message("Forwarded 10 seconds.", ephemeral=True)
        else:
            await interaction.response.send_message("No track is currently playing.", ephemeral=True)

    @discord.ui.button(emoji=f"{emojis.ICONS_MUSIC}", style=discord.ButtonStyle.secondary)
    async def replay_button(self, interaction: discord.Interaction, button: Button):
        if self.player.playing:
            await self.player.seek(0)
            await interaction.response.send_message("Replaying the current track.", ephemeral=True)
        else:
            await interaction.response.send_message("No track is currently playing.", ephemeral=True)



class Music(commands.Cog):
    def __init__(self, client: Rem):
        self.client = client
        self.lavalink_connected = False
        self.lavalink_nodes = self._load_lavalink_nodes()
        asyncio.create_task(self.connect_nodes())
        asyncio.create_task(self.monitor_inactivity())
        
        self.inactivity_timeout = 120 
        self.player_inactivity = {}  

    def _env_bool(self, name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _load_lavalink_nodes(self) -> list[dict]:
        config: dict = {}
        if os.path.exists("config.yml"):
            try:
                with open("config.yml", "r", encoding="utf-8") as fp:
                    config = yaml.safe_load(fp) or {}
            except OSError:
                log.warning("Could not read config.yml for Lavalink settings.")

        lavalink_config = config.get("LAVALINK", {}) or {}
        if not self._env_bool("LAVALINK_ENABLED", bool(lavalink_config.get("ENABLED", True))):
            return []

        raw_nodes = os.getenv("LAVALINK_NODES_JSON") or os.getenv("LAVALINK_NODES")
        if raw_nodes:
            try:
                parsed = json.loads(raw_nodes)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                if isinstance(parsed, list):
                    return [node for node in parsed if isinstance(node, dict)]
            except json.JSONDecodeError:
                log.warning("LAVALINK_NODES_JSON is not valid JSON; falling back to simple Lavalink env vars.")

        uri = os.getenv("LAVALINK_URI") or lavalink_config.get("URI")
        password = os.getenv("LAVALINK_PASSWORD") or lavalink_config.get("PASSWORD")
        if uri and password:
            return [
                {
                    "identifier": os.getenv("LAVALINK_IDENTIFIER") or lavalink_config.get("IDENTIFIER") or "main",
                    "uri": uri,
                    "password": password,
                    "heartbeat": float(os.getenv("LAVALINK_HEARTBEAT") or lavalink_config.get("HEARTBEAT", 15.0)),
                    "retries": int(os.getenv("LAVALINK_RETRIES") or lavalink_config.get("RETRIES", 3)),
                }
            ]

        config_nodes = lavalink_config.get("NODES", []) or []
        return [node for node in config_nodes if isinstance(node, dict)]

    async def _preflight_lavalink_node(self, node_config: dict) -> bool:
        uri = str(node_config.get("uri") or node_config.get("URI") or "").strip()
        password = str(node_config.get("password") or node_config.get("PASSWORD") or "").strip()
        identifier = str(node_config.get("identifier") or node_config.get("IDENTIFIER") or uri or "main")

        if not uri or not password:
            log.warning("Skipped Lavalink node %s: missing URI or password.", identifier)
            return False

        if not self._env_bool("LAVALINK_PRECHECK", True):
            return True

        info_url = urljoin(uri.rstrip("/") + "/", "v4/info")
        headers = {"Authorization": password}
        timeout = aiohttp.ClientTimeout(total=float(os.getenv("LAVALINK_PRECHECK_TIMEOUT", "8")))

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(info_url, headers=headers) as response:
                    content_type = response.headers.get("content-type", "")
                    if response.status != 200 or "json" not in content_type.lower():
                        log.warning(
                            "Skipped Lavalink node %s: %s returned HTTP %s with content-type %s.",
                            identifier,
                            info_url,
                            response.status,
                            content_type or "unknown",
                        )
                        return False
                    await response.json()
                    return True
        except Exception as exc:
            log.warning("Skipped Lavalink node %s: precheck failed for %s (%s).", identifier, info_url, exc)
            return False

    def _make_lavalink_node(self, node_config: dict) -> wavelink.Node:
        return wavelink.Node(
            identifier=str(node_config.get("identifier") or node_config.get("IDENTIFIER") or "main"),
            uri=str(node_config.get("uri") or node_config.get("URI")).rstrip("/") + "/",
            password=str(node_config.get("password") or node_config.get("PASSWORD")),
            heartbeat=float(node_config.get("heartbeat") or node_config.get("HEARTBEAT") or 15.0),
            retries=int(node_config.get("retries") or node_config.get("RETRIES") or 3),
        )

    def is_lavalink_available(self) -> bool:
        if self.lavalink_connected:
            return True
        try:
            wavelink.Pool.get_node()
            return True
        except Exception:
            return False

    def source_link_value(self, track) -> str:
        uri = getattr(track, "uri", None) or ""
        source = f"{getattr(track, 'source', '')} {uri}".lower()

        if "spotify" in source:
            emoji, label = getattr(emojis, "SPOTIFY", emojis.YOUTUBE), "Listen on Spotify"
        elif "jiosaavn" in source:
            emoji, label = emojis.JIOSAAVN, "Listen on JioSaavn"
        elif "soundcloud" in source:
            emoji, label = emojis.SOUNDCLOUD, "Listen on SoundCloud"
        else:
            emoji, label = emojis.YOUTUBE, "Listen on YouTube"

        return f"{emoji} [{label}]({uri})" if uri else f"{emoji} {label}"

    def source_name(self, track) -> str:
        source = f"{getattr(track, 'source', '')} {getattr(track, 'uri', '')}".lower()
        if "spotify" in source:
            return "Spotify"
        if "youtube" in source or "youtu.be" in source:
            return "YouTube"
        if "soundcloud" in source:
            return "SoundCloud"
        if "jiosaavn" in source:
            return "JioSaavn"
        return "Unknown Source"

    def track_link(self, track) -> str:
        title = getattr(track, "title", "Unknown track")
        uri = getattr(track, "uri", None)
        title = str(title).replace("[", "\\[").replace("]", "\\]")
        return f"[{title}]({uri})" if uri else f"**{title}**"

    async def music_reply(self, ctx: commands.Context, message: str, *, tone: str = "info") -> None:
        await ctx.send(view=music_toast(message, tone=tone))

    async def require_voice(self, ctx: commands.Context) -> bool:
        if ctx.author.voice:
            return True
        await ctx.send(view=guard_no_voice())
        return False

    async def require_same_channel(self, ctx: commands.Context, vc) -> bool:
        if ctx.author.voice and vc and ctx.author.voice.channel.id == vc.channel.id:
            return True
        await ctx.send(view=guard_same_channel())
        return False

    async def require_playing(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            await ctx.send(view=guard_not_playing())
            return None
        if not await self.require_same_channel(ctx, vc):
            return None
        return vc

    async def ensure_lavalink(self, ctx: commands.Context) -> bool:
        if self.is_lavalink_available():
            return True

        await ctx.send(view=embed_to_view(lavalink_offline_embed(emojis.ICONS_WARNING)))
        return False

    async def monitor_inactivity(self):
        try:
            await self.client.wait_until_ready()
        except RuntimeError:
            return
        while True:
            for guild in self.client.guilds:
                await self.check_inactivity(guild.id) 
            await asyncio.sleep(60) 

    async def check_inactivity(self, guild_id):
        guild = self.client.get_guild(guild_id)
        if not guild:
            return

        player = None
        for vc in self.client.voice_clients:
            if vc.guild.id == guild.id:
                player = vc
                break

        if player and player.playing and len(player.channel.members) == 1:
            await self.inactivity_timer(guild)

    async def inactivity_timer(self, guild):
        await asyncio.sleep(self.inactivity_timeout)
        if len(guild.voice_channels[0].members) == 1:
            player = None
            for vc in self.client.voice_clients:
                if vc.guild.id == guild.id:
                    player = vc
                    break
            if player:
                await player.disconnect(force=True)
                try:
                    ended = inactivity_embed()
                    if self.client.user and self.client.user.avatar:
                        ended.set_author(name="REM Music", icon_url=self.client.user.avatar.url)
                    support = Button(label="Support", style=discord.ButtonStyle.link, url="https://discord.gg/codexdev")
                    vote = Button(label="Vote", style=discord.ButtonStyle.link, url="https://top.gg/bot/1144179659735572640/vote")
                    view = View()
                    view.add_item(support)
                    view.add_item(vote)
                    await player.ctx.channel.send(view=embed_to_view(ended, view=view))
                except:
                    pass

    async def connect_nodes(self) -> None:
        try:
            await self.client.wait_until_ready()
        except RuntimeError:
            return

        if not self.lavalink_nodes:
            log.warning("Lavalink is not configured. Set LAVALINK_URI and LAVALINK_PASSWORD in .env to enable music.")
            return

        nodes: list[wavelink.Node] = []
        for node_config in self.lavalink_nodes:
            if await self._preflight_lavalink_node(node_config):
                nodes.append(self._make_lavalink_node(node_config))

        if not nodes:
            log.warning("No Lavalink nodes passed precheck. Music commands will stay disabled.")
            return

        try:
            connected = await wavelink.Pool.connect(nodes=nodes, client=self.client, cache_capacity=None)
            self.lavalink_connected = bool(connected)
            log.info("Connected Lavalink nodes: %s", ", ".join(connected.keys()) or "none")
        except Exception as exc:
            self.lavalink_connected = False
            log.warning("Failed to connect to Lavalink node(s): %s", exc)




    async def display_player_embed(self, player, track, ctx, autoplay=False):
        queue_length = len(player.queue) if getattr(player, "queue", None) else 0
        embed = player_embed(
            track,
            source_name=self.source_name(track),
            source_link=self.source_link_value(track),
            requested_by=ctx.author.display_name,
            autoplay=autoplay,
            queue_length=queue_length,
            volume=getattr(player, "volume", 100) or 100,
        )
        controls = MusicControlView(player, ctx)
        await ctx.send(view=player_layout_view(embed, controls))


    async def on_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if player is None:
            return

        ctx = getattr(player, "ctx", None)
        if not player.queue:
            if player.queue.mode == wavelink.QueueMode.loop:
                await player.play(payload.track)
                #await self.display_player_embed(player, payload.track, player.ctx)
            elif player.autoplay == wavelink.AutoPlayMode.enabled:

                await asyncio.sleep(5)

                if player.current:
                    await self.display_player_embed(player, player.current, player.ctx, autoplay=True)
                else:
                    if ctx:
                        await ctx.send("No suitable track found for autoplay.")


            else:
                await player.disconnect()
                ended = queue_ended_embed()
                if self.client.user and self.client.user.avatar:
                    ended.set_author(name="REM Music", icon_url=self.client.user.avatar.url)
                support = Button(label="Support", style=discord.ButtonStyle.link, url="https://discord.gg/codexdev")
                vote = Button(label="Vote", style=discord.ButtonStyle.link, url="https://top.gg/bot/1144179659735572640/vote")
                view = View()
                view.add_item(support)
                view.add_item(vote)
                if ctx:
                    await ctx.send(view=embed_to_view(ended, view=view))
        else:
            next_track = await player.queue.get_wait()
            await player.play(next_track)
            if ctx:
                await self.display_player_embed(player, next_track, ctx)



    async def play_source(self, ctx, query):
        if not await self.ensure_lavalink(ctx):
            return

        if not await self.require_voice(ctx):
            return

        vc = ctx.voice_client or await ctx.author.voice.channel.connect(cls=wavelink.Player)
        vc.ctx = ctx
        
        
        if vc.playing:
            if ctx.voice_client and ctx.voice_client.channel != ctx.author.voice.channel:
                await self.music_reply(
                    ctx,
                    f"I'm already in {ctx.voice_client.channel.mention}. Join that channel to add songs.",
                    tone="warning",
                )
                return
        vc.autoplay = wavelink.AutoPlayMode.disabled

        """if re.match(SPOTIFY_TRACK_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "track")
        elif re.match(SPOTIFY_PLAYLIST_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "playlist")
        elif re.match(SPOTIFY_ALBUM_REGEX, query):
            await self.handle_spotify_link(ctx, vc, query, "album")
        
            return"""
            
        tracks = await wavelink.Playable.search(query)
        if not tracks:
            await ctx.send(view=guard_no_results())
            return

        if isinstance(tracks, wavelink.Playlist):
            await vc.queue.put_wait(tracks.tracks)
            await ctx.send(
                view=music_toast(
                    f"Added playlist **{tracks.name}** with **{len(tracks.tracks)}** songs to the queue~",
                    tone="added",
                )
            )
            if not vc.playing:
                track = await vc.queue.get_wait()
                await vc.play(track)
                await self.display_player_embed(vc, track, ctx)
        else:
            track = tracks[0]
            await vc.queue.put_wait(track)
            await ctx.send(
                view=music_toast(f"Added {self.track_link(track)} to the queue~", tone="added")
            )
            if not vc.playing:
                await vc.play(await vc.queue.get_wait())
                await self.display_player_embed(vc, track, ctx)
            asyncio.create_task(self.check_inactivity(ctx.guild.id))
           # await interaction.response.defer()


    
    async def handle_spotify_link(self, ctx, vc, link, type_):
        spotify_api = get_spotify_api()
        if not spotify_api:
            await ctx.send("Spotify is not configured. Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env`.")
            return
        try:
            if type_ == "track":
                track_id = re.search(SPOTIFY_TRACK_REGEX, link).group(1)
                track_info = await spotify_api.get_track(track_id)

                
                title = track_info['name']
                author = ', '.join(artist['name'] for artist in track_info['artists'])

                
                search_query = f"{title} by {author}"
                search_results = await wavelink.Playable.search(search_query, source=wavelink.enums.TrackSource.YouTube)

                if not search_results:
                    await ctx.send("Can't play this track from Spotify, please try with another track.")
                    return

                track = search_results[0]
                await vc.queue.put_wait(track)
                await self.music_reply(ctx, f"Added {self.track_link(track)} to the queue.", tone="added")
                if not vc.playing:
                    await vc.play(track)
                    await self.display_player_embed(vc, track, ctx)

                #await self.display_player_embed(vc, track, ctx)
                
            elif type_ == "playlist":
                lmao = await ctx.send("⏳ Processing to add tracks from the playlist, this may take a while...")
                
                playlist_id = re.search(SPOTIFY_PLAYLIST_REGEX, link).group(1)
                playlist_info = await spotify_api.get(f"playlists/{playlist_id}")
                tracks = playlist_info.get("tracks", {}).get("items", [])
                playlist_length = len(tracks)

                if not tracks:
                    await ctx.send("No tracks found in the playlist.")
                    return

                c = 0
                for track in tracks:
                    title = track['track']['name']
                    author = ', '.join(artist['name'] for artist in track['track']['artists'])
                    search_query = f"{title} {author}"

                    track_results = await wavelink.Playable.search(search_query, source=wavelink.enums.TrackSource.YouTube)
                    if track_results:
                        await vc.queue.put_wait(track_results[0])
                        c += 1
                        await ctx.message.add_reaction("✅")

                await self.music_reply(
                    ctx,
                    f"Added **{c}** of **{playlist_length}** tracks from **{playlist_info['name']}**.",
                    tone="added",
                )
                await lmao.delete()
                
                if not vc.playing:
                    next_track = await vc.queue.get_wait()
                    await vc.play(next_track)
                    await self.display_player_embed(vc, next_track, ctx)


            elif type_ == "album":
                await ctx.message.add_reaction("⌛")
                album_id = re.search(SPOTIFY_ALBUM_REGEX, link).group(1)
                album_info = await spotify_api.get(f"albums/{album_id}")
                tracks = album_info.get("tracks", {}).get("items", [])

                if not tracks:
                    await ctx.send("No tracks found in the album.")
                    return

                for track in tracks:
                    title = track['name']
                    author = ', '.join(artist['name'] for artist in track['artists'])
                    search_query = f"{title} {author}"

                    track_results = await wavelink.Playable.search(search_query, source=wavelink.enums.TrackSource.YouTube)
                    if track_results:
                        await vc.queue.put_wait(track_results[0])

                await self.music_reply(ctx, f"Added all tracks from album **{album_info['name']}**.", tone="added")
                if not vc.playing:
                    next_track = await vc.queue.get_wait()
                    await vc.play(next_track)
                    await self.display_player_embed(vc, next_track, ctx)

                
        except Exception as e:
            await ctx.send(f"An error occurred while processing the Spotify link: {e}")



    @commands.hybrid_command(name="play", aliases=['p'], usage="play <query>", help="Plays a song or playlist.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def play(self, ctx: commands.Context, *, query: str):
        
        await self.play_source(ctx, query)


    @commands.hybrid_command(name="search", usage="search <query>", help="Searches music from multiple platforms.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def search2(self, ctx: commands.Context, *, query: str):
        if not await self.ensure_lavalink(ctx):
            return

        if not await self.require_voice(ctx):
            return

        embed = platform_select_embed(query)
        await ctx.send(view=embed_to_view(embed, view=PlatformSelectView(ctx, query)))


    @commands.hybrid_command(name="nowplaying", aliases=["nop"], usage="nowplaying", help="Shows the info about current playing song.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def nowplaying(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        track = vc.current
        embed = now_playing_embed(
            track,
            position=vc.position / 1000,
            queue_length=len(vc.queue) if vc.queue else 0,
            source_name=self.source_name(track),
            source_link=self.source_link_value(track),
            requested_by=ctx.author.display_name,
        )
        await ctx.send(view=embed_to_view(embed))

    @commands.hybrid_command(name="autoplay", usage="autoplay", help="Toggles autoplay mode.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def autoplay(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        vc.autoplay = (
            wavelink.AutoPlayMode.enabled if vc.autoplay != wavelink.AutoPlayMode.enabled else wavelink.AutoPlayMode.disabled
        )
        state = "enabled" if vc.autoplay == wavelink.AutoPlayMode.enabled else "disabled"
        await self.music_reply(ctx, f"Autoplay **{state}** by {ctx.author.mention}.", tone="success")

    @commands.hybrid_command(name="loop", usage="loop", help="Toggles loop mode.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def loop(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        vc.queue.mode = wavelink.QueueMode.loop if vc.queue.mode != wavelink.QueueMode.loop else wavelink.QueueMode.normal
        state = "enabled" if vc.queue.mode == wavelink.QueueMode.loop else "disabled"
        await self.music_reply(ctx, f"Loop **{state}** by {ctx.author.mention}.", tone="success")


    @commands.hybrid_command(name="pause", usage="pause", help="Pauses the current song.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pause(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        if vc.paused:
            await self.music_reply(ctx, "The player is already paused.", tone="warning")
            return

        await vc.pause(True)
        await vc.channel.edit(status=f"{emojis.MUSICSTOP_ICONS} Paused: {vc.current.title}")
        await self.music_reply(ctx, f"Paused by {ctx.author.mention}.", tone="success")

    @commands.hybrid_command(name="resume", usage="resume", help="Resumes the paused song.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def resume(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        if not vc.paused:
            await self.music_reply(ctx, "The player is not paused.", tone="warning")
            return

        await vc.pause(False)
        await vc.channel.edit(status=f"{emojis.MUSIC} Playing: {vc.current.title}")
        await self.music_reply(ctx, f"Resumed by {ctx.author.mention}.", tone="success")

    @commands.hybrid_command(name="skip", usage="skip", help="Skips the current song.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def skip(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        if vc.autoplay == wavelink.AutoPlayMode.enabled or not vc.queue.is_empty:
            await vc.stop()
            await self.music_reply(ctx, f"Skipped by {ctx.author.mention}.", tone="success")
            return

        await self.music_reply(ctx, "Nothing left in the queue to skip to.", tone="warning")

    @commands.hybrid_command(name="shuffle", usage="shuffle", help="Shuffles the queue.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def shuffle(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        if not vc.queue:
            await ctx.send(view=guard_empty_queue())
            return

        random.shuffle(vc.queue)
        await self.music_reply(ctx, f"Queue shuffled by {ctx.author.mention}.", tone="success")

    @commands.hybrid_command(name="stop", usage="stop", help="Stops the current song and clears the queue.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def stop(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        await vc.channel.edit(status=None)
        vc.queue.clear()
        await vc.disconnect(force=True)
        await self.music_reply(ctx, f"Stopped and queue cleared by {ctx.author.mention}.", tone="success")

    @commands.hybrid_command(name="volume", aliases=["vol"], usage="volume <level>", help="Sets the volume of the player.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def volume(self, ctx: commands.Context, level: int):
        vc = ctx.voice_client
        if not vc:
            await ctx.send(view=guard_not_connected())
            return

        if not await self.require_same_channel(ctx, vc):
            return

        if 1 <= level <= 150:
            await vc.set_volume(level)
            await self.music_reply(ctx, f"Volume set to **{level}%** by {ctx.author.mention}.", tone="success")
        else:
            await self.music_reply(ctx, "Volume must be between **1** and **150**.", tone="warning")

    @commands.hybrid_command(name="queue", usage="queue", help="Shows the current queue.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def queue(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.queue or vc.queue.is_empty:
            await ctx.send(view=guard_empty_queue())
            return

        if not await self.require_same_channel(ctx, vc):
            return

        entries = [queue_entry_line(index + 1, track) for index, track in enumerate(vc.queue)]
        paginator = Paginator(
            source=kawaii_queue_page_source(
                entries,
                per_page=5,
                now_playing=vc.current if vc.playing else None,
                requested_by=ctx.author.display_name,
            ),
            ctx=ctx,
        )
        await paginator.paginate()

    @commands.hybrid_command(name="clearqueue", usage="clearqueue", help="Clears the queue.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def clearqueue(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.queue or vc.queue.is_empty:
            await ctx.send(view=guard_empty_queue())
            return

        if not await self.require_same_channel(ctx, vc):
            return

        vc.queue.clear()
        await self.music_reply(ctx, "Queue cleared.", tone="success")

    @commands.hybrid_command(name="replay", usage="replay", help="Replays the current song.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def replay(self, ctx: commands.Context):
        vc = await self.require_playing(ctx)
        if not vc:
            return

        await vc.seek(0)
        await self.music_reply(ctx, "Replaying the current track from the start.", tone="success")

    @commands.hybrid_command(name="join", aliases=["connect"], usage="join", help="Joins the voice channel.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def join(self, ctx: commands.Context):
        if not await self.ensure_lavalink(ctx):
            return

        if ctx.author.voice:
            await ctx.author.voice.channel.connect(cls=wavelink.Player)
            await self.music_reply(ctx, f"Joined {ctx.author.voice.channel.mention}.", tone="success")
        else:
            await ctx.send(view=guard_no_voice())

    @commands.hybrid_command(name="disconnect", aliases=["dc", "leave"], usage="disconnect", help="Disconnects the bot from the voice channel.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def disconnect(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc:
            await ctx.send(view=guard_not_connected())
            return

        if not await self.require_same_channel(ctx, vc):
            return

        await vc.disconnect()
        await self.music_reply(ctx, "Disconnected from voice.", tone="success")

    @commands.hybrid_command(name="seek", usage="seek <percentage>", help="Seeks to a specific percentage of the song.")
    @blacklist_check()
    @ignore_check()
    @bot_has_permissions(connect=True, speak=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def seek(self, ctx: commands.Context, percentage: int):
        if not 1 <= percentage <= 100:
            await self.music_reply(ctx, "Provide a percentage between **1** and **100**.", tone="warning")
            return

        vc = await self.require_playing(ctx)
        if not vc:
            return

        track = vc.current
        target_position = int(track.length * (percentage / 100))
        await vc.seek(target_position)
        await self.music_reply(ctx, f"Seeked to **{percentage}%** of the current track.", tone="success")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player = payload.player
        if player is None or player.current is None:
            return
        track = player.current
        guild_id = player.guild.id

        voice_channel = player.channel
        if voice_channel:
            await voice_channel.edit(status=f"{emojis.MUSIC} Playing: {track.title}")  # type: ignore

        if guild_id not in track_histories:
            track_histories[guild_id] = []

        if not track_histories[guild_id] or track_histories[guild_id][-1] != track:
            track_histories[guild_id].append(track)


            if len(track_histories[guild_id]) > 10:
                track_histories[guild_id].pop(0)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if player is None:
            return
        voice_channel = player.channel

        if voice_channel:
            await voice_channel.edit(status=None)  # type: ignore
        await self.on_track_end(payload)
