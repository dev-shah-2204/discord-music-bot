import discord
import youtube_dl
import urllib.request
import re

from asyncio import sleep
from discord.ext import commands


#Static functions/variables that don't need to be in the class
pause_time = {}

playlist = {}

playlist_with_names = {}

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


async def check_if_playlist(ctx):
    guild = str(ctx.guild.id)
    if guild not in playlist:
        playlist[guild] = []
        return None

    if playlist[guild] == []:
        return None

    if len(playlist[guild]) > 0:
        return playlist[guild][0]

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
        global playlist
        global playlist_with_names

        if ctx.voice_client is None:
            await ctx.send("I'm not in a voice channel.")
            return

        await ctx.voice_client.disconnect()
        playlist[str(ctx.guild.id)] = []  # Reset the playlist
        playlist_with_names[str(ctx.guild.id)] = []  # Reset the playlist
        await ctx.message.add_reaction("👋")


    async def wait_until_song_complete(self, ctx, args):
        """
        Function to check every few seconds
        if the voice client is done playing
        a song.
        """
        global playlist
        global playlist_with_names

        vc = ctx.voice_client
        guild = str(ctx.guild.id)

        # Adding guild id in the playlist dictionaries
        if guild not in playlist:
            playlist[guild] = []

        if guild not in playlist_with_names:
            playlist_with_names[guild] = []

        # Checking different states of the voice client
        if vc is None:
            return

        if vc.is_playing():  # If something is being played
            if args not in playlist[guild]:
                playlist[guild].append(args)

                if not args.startswith("https://") or not args.startswith("http://"):
                    song = await find_song(args)
                    if song is None:
                        await ctx.send("Couldn't find that on YouTube.")
                        return
                else:
                    song = args

                song_title = await get_title(song)

                if song_title is None:
                    await ctx.send("Couldn't find that on YouTube.")
                    return


                em = discord.Embed(
                    title="Added song to playlist",
                    description=song_title,
                    color=0x60FF60
                )
                await ctx.send(embed=em)
                playlist_with_names[guild].append(song_title)

            await sleep(3)  # Check every 3 seconds. I know it's not a very good method.
            await self.wait_until_song_complete(ctx, args)

        if vc.is_paused():
            if guild not in pause_time:
                pause_time[guild] = 0
            else:
                pause_time[guild] += 5

            if pause_time[guild] > 120:
                await ctx.send("I was paused for more than 2 minutes, so I left the voice channel. Your playlist has been cleared")
                if guild in playlist:
                    playlist[guild] = []

                return

            await sleep(5)
            await self.wait_until_song_complete(ctx, args)

        else:  # If the voice client is idle
            try:
                song = playlist[guild][0]
                song_title = playlist_with_names[guild][0]
            except IndexError:
                playlist[guild].append(args)

                if not args.startswith("https://") or not args.startswith("http://"):
                    song = await find_song(args)
                    if song is None:
                        await ctx.send("Couldn't find that on YouTube.")
                        return
                else:
                    song = args

                song_title = await get_title(song)

            try:
                await self.play_song(ctx, song)
                del song
                del song_title

            except discord.ClientException or discord.errors.ClientException:
                await sleep(1)  # Try again in a second
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

        if voice is None:
            await ctx.send("I'm not in a voice channel.")
            return

        voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice.channel

        if voice_channel != bot_voice_channel:
            await ctx.send("You need to be in the same voice channel as me to run that command.")


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

        if voice is None:
            await ctx.send("I'm not in a voice channel.")
            return

        voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice.channel

        if voice_channel != bot_voice_channel:
            await ctx.send("You need to be in the same voice channel as me to run that command.")

        if voice.is_playing():
            voice.stop()

            try:
                if str(ctx.guild.id) in playlist:
                    del playlist[str(ctx.guild.id)][0]  # Remove that song from the playlist

                if str(ctx.guild.id) in playlist_with_names:
                    del playlist_with_names[str(ctx.guild.id)][0]  # Remove that song from the playlist

            except IndexError:
                pass

            await ctx.send(f"Song skipped by {ctx.author.mention}")

        if voice.is_paused():
            voice.resume()
            voice.stop()

            try:
                if str(ctx.guild.id) in playlist:
                    del playlist[str(ctx.guild.id)][0]  # Remove that song from the playlist

                if str(ctx.guild.id) in playlist_with_names:
                    del playlist_with_names[str(ctx.guild.id)][0]  # Remove that song from the playlist

            except IndexError:
                pass

            await ctx.send(f"Song skipped by {ctx.author.mention}")

        check = await check_if_playlist(ctx)

        if check is None:
            return
        else:
            await self.wait_until_song_complete(ctx, check)


    @commands.command(name="playlist", aliases=["q","queue"], help="Show the upcoming songs")
    async def queue(self, ctx):
        global playlist_with_names

        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to run that command")
            return

        voice = ctx.voice_client

        if voice is None:
            await ctx.send("I'm not in a voice channel")
            return

        voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice.channel

        if voice_channel != bot_voice_channel:
            await ctx.send("You need to be in the same voice channel as me to run that command.")
            return


        if str(ctx.guild.id) not in playlist_with_names:
            await ctx.send("The playlist is empty")
            return

        else:
            add_footer = False
            desc = ""
            i = 1

            await ctx.send("Hang on, playlist loading.")

            for song in playlist_with_names[str(ctx.guild.id)]:
                print(song)
                desc += f"{i}. {song}\n"
                i += 1


            if desc != "":
                em = discord.Embed(
                    title="Upcoming songs:",
                    description=desc,
                    color=0x60FF60
                )

            if desc == "":
                await ctx.send("The playlist is empty")
                return

            await ctx.send(embed=em)



def setup(bot):
    bot.add_cog(Music(bot))
    print("Music cog loaded")
