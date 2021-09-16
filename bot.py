import discord
import os

from cogs import music
from discord.ext import commands


class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='mb ' and 'mb!',
            intentes=discord.Intents.all(),
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(everyone=False),
            owner_id=416979084099321866
        )

    async def on_ready(self):
        print("^_^")
        print(f"Logged in as {self.user}")
        print(f"ID: {self.user.id}")




