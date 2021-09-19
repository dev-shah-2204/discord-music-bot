import os
from bot import MusicBot


cogs = [
    'music',
    'error_handler',
    'info'
]

bot = MusicBot(prefix="m!")

for cog in cogs:
    if __name__ == "__main__":
        try:
            bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            print(e)

bot.run(os.environ.get('MusicBotToken'))