# -*- coding: utf-8 -*-

import discord
import os
import random

from datetime import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv
from pickledb import PickleDB

SEARCH_MAX_LENGTH = 5
WANTLIST_MAX_LENGTH = 20
DRAFT_ROUNDS = 42

load_dotenv()

card_data  = PickleDB('cards.db')
user_data  = PickleDB('users.db')
draft_data = PickleDB('draft.db')

# card_data is indexed by lowercase version of card name
def get_card(card_id):
    return card_data.get(card_id.lower())

# user_id is provided by discord and coerced to string by pickleDB
def get_user(user_id):
    return user_data.get(user_id)

def search_cards(fragment):
    fragment = fragment.lower()

    ret = []
    for card_id in card_data.all():
        if fragment in card_id:
            ret.append(get_card(card_id))

        if len(ret) >= SEARCH_MAX_LENGTH:
            break

    return ret

if not draft_data.get('current-round'):
    draft_data.set('current-round', 1)
    draft_data.set('has-started', False)
    draft_data.set('has-finished', False)
    draft_data.set('number-of-rounds', DRAFT_ROUNDS)
    draft_data.set('current-position', None)
    draft_data.set('snaking-forwards', True)
    draft_data.set('pick-order', [])
    draft_data.save()

    with open('card-list.txt', 'r') as f:
        for card_name in f.read().splitlines():
            card_id = card_name.lower()
            card_data.set(card_id, {'id': card_id, 'name': card_name, 'taken': False})

    card_data.save()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='', intents=intents)

@bot.command()
async def register(ctx, *, args):
    # check if the user is already registered
    if get_user(ctx.author.id):
        await ctx.send('ERROR: You\'re already registered!')
        return

    if len(args.split()) <= 1:
        await ctx.send('ERROR: You need to specify a team name and a 3 character abbreviation!\ne.g. register The Pheliadelphia Doggos PHL')
        return

    # Split team name and abbreviation. First 3 characters of last word is their abbreviation
    # EG: Los Angeles Lanturns LAL
    team_abbreviation = args.split()[-1].upper()
    team_name = ' '.join(args.split()[0:-1])
    if len(team_abbreviation) > 3:
        team_abbreviation = team_abbreviation[0:3]
    if len(team_abbreviation) < 3:
        await ctx.send('ERROR: Your abbreviation should be 3 characters!')
        return

    # Reject the user if the team name or abbreviation is already in use
    for user_id in user_data.all():
        user = get_user(user_id)
        if team_name == user['team-name']:
            await ctx.send('ERROR: That team name is already in use! Pick another one, please.')
            return
        if team_abbreviation == user['team-abbreviation']:
            await ctx.send('ERROR: That abbreviation is already in use! Pick another one, please.')
            return

    # registration looks good, so create and store a new user dict
    new_user = {
        'discord-id': ctx.author.id,
        'discord-name': ctx.author.name,
        'discord-discriminator': ctx.author.discriminator,

        'team-name': team_name,
        'team-abbreviation': team_abbreviation,
        'drafted-cards': [],
        'wanted-cards': []
    }

    user_data.set(ctx.author.id, new_user)
    user_data.save()

    await ctx.send(f'Your team, {team_name} ({team_abbreviation}), has been registered. Congratulations!\nWelcome to secret samp scubing. Happy dueling!')

@bot.command()
async def start_draft(ctx):
    # if the draft has already finished, this command should be rejected
    if draft_data.get('has-finished') == True:
        await ctx.send('ERROR: The draft already finished. If you want to run a new draft, kill the bot and then delete db files.')
        return

    # If the draft has been started, this command should be rejected
    if draft_data.get('has-started') == True:
        await ctx.send('ERROR: The draft has already been started.')
        return

    draft_data.set('has-started', True)
    draft_data.set('current-position', 0)
    draft_data.set('time-began', str(datetime.now()))

    # get a random ordering of users
    pick_order = list(user_data.all())
    random.shuffle(pick_order)

    pick_order_string = ', '.join(map(lambda user_id:get_user(user_id)['discord-name'], pick_order))

    draft_data.set('pick-order', pick_order)
    draft_data.save()

    await ctx.send(f'The draft has been started!\nThe draft order is: {pick_order_string}')

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
    if draft_data.get('has-finished') == True:
        await ctx.send('ERROR: The draft already finished. If you want to run a new draft, kill the bot and then delete db files.')
        return

    # block excessive wantlist for efficiency purposes
    if len(user['wanted-cards']) >= WANTLIST_MAX_LENGTH:
        await ctx.send('ERROR: Your draft list is too long. Please remove some cards before trying to draft more. !clear to wipe list')
        return

    # cannot want a card that has already been taken
    if card['taken']:
        await ctx.send('ERROR: Card already taken')
        return

    user['wanted-cards'].append(card['id'])
    user_data.save()

    wanted_cards_string = ', '.join(map(lambda card_id:get_card(card_id)['name'], user['wanted-cards']))

    await ctx.send(f'Draftlist Updated: {wanted_cards_string}')

@bot.command()
async def clear(ctx):
    user = get_user(ctx.author.id)

    if not user:
        await ctx.send('ERROR: Not registered. Try the !register command')
        return

    user['wanted-cards'] = []
    user_data.save()

    await ctx.send('Draftlist Wiped')

@bot.command()
async def search(ctx, *, args):
    card_list = search_cards(args)

    if len(card_list):
        await ctx.send(', '.join(map(lambda card:card['name'], card_list)))
    else:
        await ctx.send(f'No cards found matching {args}')

@tasks.loop(seconds=5)
async def attempt_draft():
    print('Attempting to perform draft')

@bot.event
async def on_ready():
    print('Bot is ready!')
    attempt_draft.start()

bot.run(os.getenv('DISCORD_TOKEN'))
