# mtgDiscordBot

Discord Bot used to automate and manage MTG Rotisserie Draft Leagues.

Tested on Python 3.12.11

--------------------------------------------------------------------------------------------------

Features:
- Can be used to manage an arbitrary number of players conducting a rotisserie draft (aka snake draft).
- Allows for queuing of picks ahead of time.
  - Keep your draft running quickly by queuing multiple picks in a row.
  - In the event that another player drafts one of your queued choices, you will be alerted. (TODO)

--------------------------------------------------------------------------------------------------

TODO:
- Handle API failures gracefully

--------------------------------------------------------------------------------------------------

Setup:

To set up the bot, you need to register a new bot on the Discord app page, get a token, etc. There are plenty of guides for this available. The token will be used to connect the bot to your server. You must edit the .env file with your token

The app and supporting data file (bot.py, card-list.txt) must be placed in a directory together. The Python app needs to run indefinitely, as long as the draft is running. I would recommend using `screen` or `nohup` to accomplish this.

In the event that the bot crashes due to Discord outages/hiccups, simply restart the app; your draft will be able to resume from its previous position. These issues are thankfully infrequent enough that this shouldn't be an issue.

All participating players will need to register with the `!register` command before the draft begins. Use the `!help` (TODO) command for more info.
