import discord
import youtube_dl
import urllib.request
import re

from asyncio import sleep
from discord.ext import commands


# Helper functions
sent_embed = {

}

playlist = {

}

FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

YDL_OPTIONS = {
    'format': 'bestaudio',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }]
}

async def get_title(url):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info['title']
        return title

async def find_song(args):
    args = args.replace(' ', '+')
    html_content = urllib.request.urlopen(f"https://youtube.com/results?search_query={args}")  # YouTube's search link structure
    video_ids = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())  # Each video has a unique ID, 11 characters long.

    try:
        args = f"https://youtube.com/watch?v={video_ids[0]}"
        return args

    except KeyError:  # If video_ids[0] doesn't exist
        return None


# Main cog
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="join", help="Make the bot join a voice channel")
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to run that command")
            return

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            await voice_channel.connect()
            return
        else:
            await ctx.voice_client.move_to(voice_channel)


    @commands.command(name="leave", aliases=["fuckoff"], help="Make the bot leave a voice channel")
    async def leave(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("I'm not in a voice channel.")
            return

        await ctx.voice_client.disconnect()
        await ctx.message.add_reaction("👋")


    async def wait_until_song_complete(self, ctx, args):
        # Code written with really bad logic. Forgive me.
        vc = ctx.voice_client

        if vc is None:  # If they made the bot leave the voice channel before the function was re-called
            return

        if vc.is_playing():
            # Really bad logic. I know. I couldn't find another way.
            if str(ctx.guild.id) not in sent_embed:
                sent_embed[str(ctx.guild.id)] = []

            if args not in sent_embed[str(ctx.guild.id)]:
                if str(ctx.guild.id) not in playlist:
                    playlist[str(ctx.guild.id)] = []
                    playlist[str(ctx.guild.id)].append(args)

                else:
                    if args not in playlist[str(ctx.guild.id)]:
                        playlist[str(ctx.guild.id)].append(args)


                if args.startswith("https://") or args.startswith("http://"):
                    song = await get_title(args)  # So that we can get the song title
                else:
                    song = await get_title(await find_song(args))  # Just use the name that the user passed

                em = discord.Embed(
                    title="Added song to playlist",
                    description=song,
                    color=0x60FF60
                )

                sent_embed[str(ctx.guild.id)].append(args)
                await ctx.send(embed=em)


            await sleep(3)  # Check every 3 seconds
            await self.wait_until_song_complete(ctx, args)


        else:
            if str(ctx.guild.id) not in playlist:  # If it's the first time the command was run, guild id won't be in the dict
                playlist[str(ctx.guild.id)] = []
                playlist[str(ctx.guild.id)].append(args)

            try:
                await self.play_song(ctx, playlist[str(ctx.guild.id)][0])
                playlist[str(ctx.guild.id)].remove(args)

            except discord.ClientException:
                await self.wait_until_song_complete(ctx, args)



    async def play_song(self, ctx, args):
        vc = ctx.voice_client

        if not args.startswith("https://") or not args.startswith("http://"):
            args = await find_song(args)

        if args is not None:
            try:
                with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(args, download=False)

                if info['duration'] > 1200:
                    await ctx.send("You cannot play videos longer than 20 minutes.")
                    return

                url = info['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                vc.play(source)

                em = discord.Embed(
                    title="Now Playing",
                    description=f"[{info['title']}]({args})",
                    color=0x60FF60
                )
                em.set_image(url=info['thumbnail'])
                await ctx.send(embed=em)

            except youtube_dl.utils.DownloadError:
                await ctx.send("There was an error playing from the given arguements.")

            except discord.errors.ClientException or discord.ClientException:
                playlist[str(ctx.guild.id)].append(args)
        else:
            await ctx.send("I couldn't find that song/video.")



    @commands.command(name="play", aliases=["p"], help="Play a song.")
    async def play(self, ctx, *, args:str):
        await self.join(ctx)
        await self.wait_until_song_complete(ctx, args)


    @commands.command(name="pause", help="Pause a song.")
    async def pause(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to run that command")
            return

        voice = ctx.voice_client

        voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice.channel

        if voice_channel != bot_voice_channel:
            await ctx.send("You need to be in the same voice channel as me to run that command.")

        if voice is None:
            await ctx.send("I'm not connected to a voice channel")
            return

        if voice.is_playing():
            voice.pause()
            await ctx.send(f"⏸️ Paused")
        else:
            await ctx.send("No audio is being played.")


    @commands.command(name="resume", help="Resume a paused song.")
    async def resume(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to run that command")
            return

        voice = ctx.voice_client

        voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice.channel

        if voice_channel != bot_voice_channel:
            await ctx.send("You need to be in the same voice channel as me to run that command.")

        if voice is None:
            await ctx.send("I'm not in a voice channel")
            return

        if voice.is_paused():
            await ctx.message.add_reaction("▶️")
            voice.resume()
        else:
            await ctx.send("No audio is being played.")


    @commands.command(name="stop", help="Stop playing a song. Completely.")
    async def stop(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to run that command")
            return

        voice = ctx.voice_client

        voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice.channel

        if voice_channel != bot_voice_channel:
            await ctx.send("You need to be in the same voice channel as me to run that command.")

        if voice is not None:
            await ctx.message.add_reaction("⏹️")
            voice.stop()
        else:
            await ctx.send("I'm not in a voice channel")

    @commands.command(name="skip", help="Skip a song")
    async def skip(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to run that command")
            return

        voice = ctx.voice_client

        voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice.channel

        if voice_channel != bot_voice_channel:
            await ctx.send("You need to be in the same voice channel as me to run that command.")

        if voice is not None:
            if voice.is_playing():
                voice.stop()
                await ctx.send(f"Song skipped by {ctx.author.mention}")

            if voice.is_paused():
                pass

        else:
            await ctx.send("I'm not in a voice channel.")


    @commands.command(name="playlist", aliases=["q","queue"], help="Show the upcoming songs")
    async def queue(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to run that command")
            return

        voice = ctx.voice_client

        voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice.channel

        if voice_channel != bot_voice_channel:
            await ctx.send("You need to be in the same voice channel as me to run that command.")
            return

        if voice is None:
            await ctx.send("I'm not in a voice channel")
            return

        if str(ctx.guild.id) not in playlist:
            await ctx.send("The playlist is empty")
            return

        else:
            add_footer = False
            desc = ""
            i = 1

            for song in playlist[str(ctx.guild.id)]:
                if song.startswith("https://") or song.startswith("http://"):
                    song = await get_title(song)
                else:
                    song = await get_title(await find_song(song))

                if song is not None:
                    desc += f"{i}. {song}\n"
                    i += 1
                if song is None:
                    add_footer = True

            if desc != "":
                em = discord.Embed(
                    title="Upcoming songs:",
                    description=desc,
                    color=0x60FF60
                )
            if add_footer is True:
                em.set_footer(text="Missing songs? That might be because I couldn't find them from the URL/keywords you provided.")

            if desc == "":
                await ctx.send("The playlist is empty")
                return

            await ctx.send(embed=em)



def setup(bot):
    bot.add_cog(Music(bot))
    print("Music cog loaded")
