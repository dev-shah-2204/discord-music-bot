import discord
import youtube_dl
import urllib.request
import re

from discord.ext import commands


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


    @commands.command(name="play", aliases=["p"], help="Play a song.")
    async def play(self, ctx, *, args:str):
        await self.join(ctx)

        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        YDL_OPTIONS = {
            'format': 'bestaudio',
            #'outtmpl': f"./music/{ctx.guild.id}.mp3",
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                }
            ]
        }

        vc = ctx.voice_client

        if not args.startswith("https://") or not args.startswith("http://"):
            args = args.replace(' ', '+')
            html_content = urllib.request.urlopen(f"https://youtube.com/results?search_query={args}")
            video_ids = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())

            try:
                args = f"https://youtube.com/watch?v={video_ids[0]}"
            except KeyError:
                await ctx.send(f"No results were found for that.")


        try:
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(args, download=False)
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
            await ctx.send("There was an error. Are you sure that is the correct URL?")

        except discord.errors.ClientException:
            vc.stop()
            try:
                vc.play(source)
            except youtube_dl.utils.DownloadError:
                await ctx.send("There was an error. Are you sure that is the correct URL?")




    @commands.command(name="pause", help="Pause a song.")
    async def pause(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice is None:
            await ctx.send("Bruh I'm not even in a VC smh.")
            return

        if voice.is_playing():
            voice.pause()
            await ctx.send(f"⏸️ Paused")
        else:
            await ctx.send("No audio is being played.")


    @commands.command(name="resume", help="Resume a paused song.")
    async def resume(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

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
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice is not None:
            await ctx.message.add_reaction("⏹️")
            voice.stop()
        else:
            await ctx.send("I'm not in a voice channel")


def setup(bot):
    bot.add_cog(Music(bot))
    print("Music cog loaded")
