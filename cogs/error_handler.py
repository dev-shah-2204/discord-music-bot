import discord

from discord.ext import commands


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ctx.author.mention}, that command is incomplete")
            ctx.command.reset_cooldown(ctx)
            return

        elif isinstance(error, commands.BotMissingPermissions):
            perm = error.missing_perms[0].title().replace('_', ' ')

            await ctx.send(f"{ctx.author.mention}, I need the `{perm}` permission in order to complete that command")
            ctx.command.reset_cooldown(ctx)
            return

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Hold your horses, that command is still on cooldown ({error.retry_after:,.1f} seconds)")
            return

        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"`{error.args}` cannot be the argument for that command. Please run `m!help {ctx.command}`")
            return

        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Did you make a typo? Because that command doesn't exist")
            return

        elif isinstance(error, discord.Forbidden) or isinstance(error, discord.errors.Forbidden):
            await ctx.send("Uh-oh, an error occurred. An easy fix is to give me the `Embed Links` permission. If that doesn't work, please contact StatTrakDiamondSword#5493")

        else:
            await ctx.send("An error occured that I wasn't able to handle myself. This has been conveyed to my developer.")
            channel = self.bot.get_channel(857878860251136020)

            em = discord.Embed(
                title="Error",
                description=f"```Command: {ctx.command}\nServer: {ctx.guild} ({ctx.guild.id})\nChannel: {ctx.channel} ({ctx.channel.id})\nUser: {ctx.author} ({ctx.author.id})```",
                color=0xFF3E3E
            )
            em.add_field(name="Message:", value=ctx.message.content, inline=False)
            em.add_field(name="Error", value=f"```{error}```")

            if channel is not None:
                await channel.send(embed=em)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
    print("ErrorHandler cog loaded")
