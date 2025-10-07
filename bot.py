# -*- coding: utf-8 -*-

import discord
import os

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

MAIN_DATA = {
    'users': [], 
    'availableCards': [],
    'draftStarted': False,
    'draftFinished': False,
    'draftRound': 1,
    'numberOfDraftRounds': 11,
    'draftCurrentPosition': None,
    'draftGoingForwards': True,
    'draftOrder': []
}

with open('cardList.txt', 'r') as f:
    MAIN_DATA['availableCards'] = f.read().splitlines()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='', intents=intents)

@bot.command()
async def register(ctx, *, args):
    global MAIN_DATA

    # check if the user is already registered
    for iterUser in MAIN_DATA['users']:
        if ctx.author.id == iterUser['discord_id']:
            await ctx.send("ERROR: You're already registered!")
            return

    if len(args.split()) <= 1:
        await ctx.send('ERROR: You need to specify a team name and a 3 character abbreviation!\ne.g. register Pheliadelphia Doggos PHL')
        return

    # Split team name and abbreviation. First 3 characters of last word is their abbreviation
    # EG: Los Angeles Lanturns LAL
    inputAbbreviation = args.split()[-1].upper()
    inputTeamName = ' '.join(args.split()[0:-1])
    if len(inputAbbreviation) > 3:
        inputAbbreviation = inputAbbreviation[0:3]
    if len(inputAbbreviation) < 3:
        await ctx.send('ERROR: Your abbreviation should be 3 characters!')
        return

    # Reject the user if the team name or abbreviation is already in use
    for iterUser in MAIN_DATA['users']:
        if inputTeamName == iterUser['teamName']:
            await ctx.send('ERROR: That team name is already in use! Pick another one, please.')
            return
        if inputAbbreviation == iterUser['teamAbbreviation']:
            await ctx.send('ERROR: That abbreviation is already in use! Pick another one, please.')
            return

    # registration looks good, so create and store a new user dict
    newUser = {}

    newUser['discord_id'] = ctx.author.id
    newUser['discord_name'] = ctx.author.name
    newUser['discord_discriminator'] = ctx.author.discriminator

    newUser['teamName'] = inputTeamName
    newUser['teamAbbreviation'] = inputAbbreviation
    newUser['teamMembers'] = []
    newUser['draftList'] = []

    MAIN_DATA['users'].append(newUser)
    
    print(MAIN_DATA)

    await ctx.send(f'Your team, The {inputTeamName}, has been registered. Congratulations!\nWelcome to secret samp scubing. Happy dueling!')

bot.run(os.getenv('TOKEN'))
