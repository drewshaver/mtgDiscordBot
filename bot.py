# -*- coding: utf-8 -*-

import discord
import os
import random

from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
from pickledb import PickleDB

SEARCH_MAX_LENGTH = 5
WANTLIST_MAX_LENGTH = 20
DRAFT_ROUNDS = 42

load_dotenv()

card_data = PickleDB('cards.db')
main_data = PickleDB('main.db')
user_data = PickleDB('users.db')

# cardID is lowercase version of the card name
def get_card(cardID):
    return card_data.get(cardID.lower())

# userID is provided by discord and coerced to string by pickleDB
def get_user(userID):
    return user_data.get(userID)

def search_cards(fragment):
    fragment = fragment.lower()

    ret = []
    for cardID in card_data.all():
        if fragment in cardID:
            ret.append(get_card(cardID))

        if len(ret) >= SEARCH_MAX_LENGTH:
            break

    return ret

if not main_data.get('draftRound'):
    main_data.set('draftStarted', False)
    main_data.set('draftFinished', False)
    main_data.set('draftRound', 1)
    main_data.set('numberOfDraftRounds', DRAFT_ROUNDS)
    main_data.set('draftCurrentPosition', None)
    main_data.set('draftGoingForwards', True)
    main_data.set('draftOrder', [])
    main_data.save()

    with open('cardList.txt', 'r') as f:
        for cardName in f.read().splitlines():
            cardID = cardName.lower()
            card_data.set(cardID, {'id': cardID, 'name': cardName, 'taken': False})
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

    draftOrderString = ', '.join(map(lambda userID:get_user(userID)['discord_name'], draftOrder))

    main_data.set('draftOrder', draftOrder)
    main_data.save()

    await ctx.send(f'The draft has been started!\nThe draft order is: {draftOrderString}')

@bot.command()
async def draft(ctx, *, args):
    user = get_user(ctx.author.id)
    card = get_card(args)

    if not user:
        await ctx.send('ERROR: Not registered. Try the !register command')
        return

    # ensure a clear match before proceeding
    #   either an exact string match (in which case card is already populated)
    #   or use the card from search if there is exactly 1 match
    if not card:
        card_list = search_cards(args)

        if len(card_list) == 0:
            await ctx.send('ERROR: No matching cards found. Try !search to resolve')
            return

        if len(card_list) > 1:
            card_list_string = ', '.join(map(lambda card:card['name'], card_list))
            await ctx.send(f'ERROR: Multiple matching cards found. Please be precise\nMatches: {card_list_string}')
            return

        card = card_list[0]

    # if the draft has already finished, this command should be rejected
    if main_data.get('draftFinished') == True:
        await ctx.send('ERROR: The draft already finished. If you want to run a new draft, kill the bot and then delete db files.')
        return

    # block excessive wantlist for efficiency purposes
    if len(user['wantedCards']) >= WANTLIST_MAX_LENGTH:
        await ctx.send('ERROR: Your draft list is too long. Please remove some cards before trying to draft more. !clear to wipe list')
        return

    # cannot want a card that has already been taken
    if card['taken']:
        await ctx.send('ERROR: Card already taken')
        return

    user['wantedCards'].append(card['id'])
    user_data.save()

    wantedCardsString = ', '.join(map(lambda cardID:get_card(cardID)['name'], user['wantedCards']))

    await ctx.send(f'Draftlist Updated: {wantedCardsString}')

@bot.command()
async def clear(ctx):
    user = get_user(ctx.author.id)

    if not user:
        await ctx.send('ERROR: Not registered. Try the !register command')
        return

    user['wantedCards'] = []
    user_data.save()

    await ctx.send('Draftlist Wiped')

@bot.command()
async def search(ctx, *, args):
    card_list = search_cards(args)

    if len(card_list):
        await ctx.send(', '.join(map(lambda card:card['name'], card_list)))
    else:
        await ctx.send(f'No cards found matching {args}')

bot.run(os.getenv('TOKEN'))
