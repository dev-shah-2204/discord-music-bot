import os
from bot import MusicBot

FFMPEG_DOWNLOAD_URL = "https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git"  # For heroku

cogs = [
    'music'
]

bot = MusicBot()

for cog in cogs:
    if __name__ == "__main__":
        try:
            bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            print(e)

bot.run(os.environ.get('MusicBotToken'))