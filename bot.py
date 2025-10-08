# -*- coding: utf-8 -*-

import discord
import os
import random

from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
from pickledb import PickleDB

load_dotenv()

card_data = PickleDB('cards.db')
main_data = PickleDB('main.db')
user_data = PickleDB('users.db')

# currently, cardID is lowercase version of the card name
def get_card(cardID):
    return card_data.get(cardID)

# userID is provided by discord and coerced to string by pickleDB
def get_user(userID):
    return user_data.get(userID)

if not main_data.get('draftRound'):
    main_data.set('draftStarted', False)
    main_data.set('draftFinished', False)
    main_data.set('draftRound', 1)
    main_data.set('numberOfDraftRounds', 11)
    main_data.set('draftCurrentPosition', None)
    main_data.set('draftGoingForwards', True)
    main_data.set('draftOrder', [])
    main_data.save()

    with open('cardList.txt', 'r') as f:
        for cardName in f.read().splitlines():
            card_data.set(cardName.lower(), {'name': cardName, 'taken': False})
    card_data.save()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='', intents=intents)

@bot.command()
async def register(ctx, *, args):
    # check if the user is already registered
    for userID in user_data.all():
        # pickleDB has already coerced userID to a string before saving
        if str(ctx.author.id) == userID:
            await ctx.send('ERROR: You\'re already registered!')
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
    for userID in user_data.all():
        user = get_user(userID)
        if inputTeamName == user['teamName']:
            await ctx.send('ERROR: That team name is already in use! Pick another one, please.')
            return
        if inputAbbreviation == user['teamAbbreviation']:
            await ctx.send('ERROR: That abbreviation is already in use! Pick another one, please.')
            return

    # registration looks good, so create and store a new user dict
    newUser = {}

    newUser['discord_id'] = ctx.author.id
    newUser['discord_name'] = ctx.author.name
    newUser['discord_discriminator'] = ctx.author.discriminator

    newUser['teamName'] = inputTeamName
    newUser['teamAbbreviation'] = inputAbbreviation
    newUser['draftedCards'] = []
    newUser['wantedCards'] = []

    user_data.set(ctx.author.id, newUser)
    user_data.save()

    await ctx.send(f'Your team, The {inputTeamName}, has been registered. Congratulations!\nWelcome to secret samp scubing. Happy dueling!')

@bot.command()
async def start_draft(ctx):
    # if the draft has already finished, this command should be rejected
    if main_data.get('draftFinished') == True:
        await ctx.send('ERROR: The draft already finished. If you want to run a new draft, kill the bot and then delete db files.')
        return

    # If the draft has been started, this command should be rejected
    if main_data.get('draftStarted') == True:
        await ctx.send('ERROR: The draft has already been started.')
        return

    main_data.set('draftStarted', True)
    main_data.set('draftCurrentPosition', 0)
    main_data.set('timeDraftBegan', str(datetime.now()))
    main_data.set('timeOfLastDraft', str(datetime.now()))

    # get a random ordering of users
    draftOrder = list(user_data.all())
    random.shuffle(draftOrder)
    
    draftOrderString = list(map(lambda userID: get_user(userID)['discord_name'], draftOrder))

    main_data.set('draftOrder', draftOrder)
    main_data.save()

    await ctx.send(f'The draft has been started!\nThe draft order is: {draftOrderString}')

bot.run(os.getenv('TOKEN'))
