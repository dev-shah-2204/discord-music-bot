import discord

from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping', help="Show the bot's ping")
    async def ping(self, ctx):
        em = discord.Embed(
            title="Pong!",
            description=f"{round(self.bot.latency*1000)} ms",
            color=0x60FF60
        )

        await ctx.send(embed=em)


    @commands.command(name="invite", help="Get the bot's invite link")
    async def invite(self, ctx):
        em = discord.Embed(
            title="Thanks for inviting me!",
            description=f"Click [here](https://discord.com/api/oauth2/authorize?client_id={self.bot.id}&permissions=446680124480&scope=bot)!",
            color=0x60FF60
        )

        await ctx.send(embed=em)


    @commands.command(name="stats", help="Get the bot's stats")
    async def stats(self, ctx):
        em = discord.Embed(
            title="Here are my stats!",
            description="They are very accurate",
            color=0x60FF60
        )
        em.add_field(
            name="Servers:",
            value=len(self.bot.guilds),
            inline=False
        )
        em.add_field(
            name="Active voice channels",
            value=len(self.bot.voice_clients),
            inline=False
        )

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Info(bot))
    print("Info cog loaded")
