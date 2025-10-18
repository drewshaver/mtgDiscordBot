# mtgDiscordBot

Discord Bot used to automate and manage MTG Rotisserie Draft Leagues.

Tested on Python 3.12.11

--------------------------------------------------------------------------------------------------

Features:
- Can be used to manage an arbitrary number of players conducting a rotisserie draft (aka snake draft).
- (optional) Relays picks into a google spreadsheet derived from Lucky Paper's Rotisserie Draft Template for easy viewing
- Allows for queuing of picks ahead of time.
  - Keep your draft running quickly by queuing multiple picks in a row.

--------------------------------------------------------------------------------------------------

TODO:
- Handle API failures gracefully
- Alert players if their planned pick is taken
- Allow customization around persistence, some users may want the list reset after 1 or 2 picks

--------------------------------------------------------------------------------------------------

Setup:

To set up the bot, you need to register a new bot on the Discord app page, get a token, etc. There are plenty of guides for this available. The token will be used to connect the bot to your server. You must edit the .env file with your token

If you are using the spreadsheet export, you need a JWT configured for authentication from Google Cloud API services. Store the key file in `google-cloud-credentials.json`. Here is a guide to set that up: https://docs.gspread.org/en/latest/oauth2.html#service-account. Remember to share edit access on the spreadsheet with your IAM user at Google Cloud.

The app and supporting data file (bot.py, card-list.txt) must be placed in a directory together. The Python app needs to run indefinitely, as long as the draft is running. I would recommend using `screen` or `nohup` to accomplish this.

In the event that the bot crashes due to Discord outages/hiccups, simply restart the app; your draft will be able to resume from its previous position. These issues are thankfully infrequent enough that this shouldn't be an issue.

All participating players will need to register with the `!register` command before the draft begins. Use the `!help` command for more info.
