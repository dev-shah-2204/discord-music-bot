# Discord Music Bot

Discord bot written in python that can play music in voice channels.

# Setup
From this repository, download everything except: </br>
`.gitignore` </br>
`LICENSE` </br>
`Procfile` (unless you wish to host this bot on heroku)</br>


The setup is quite simple. You need [ffmpeg](https://ffmpeg.org/download.html). Then go to the bin folder and copy the 3 executable files (if you're on windows) and paste them in your bot's folder. Then setup an environment variable called "MusicBotToken" or simply change the value of token in `main.py`.

Now this part is optional, in the end of the `error_handler.py` file, you'll see a variable called channel. Change that value to a channel ID where you'd like to see the unhandled errors pop up, and also change the "StatTrakDiamondSword#5493" to your discord username (it's in the `error_handler.py` file).

That's it!
