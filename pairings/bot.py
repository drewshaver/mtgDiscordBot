# -*- coding: utf-8 -*-

import discord
import os
import random

from discord.ext import commands, tasks
from dotenv import load_dotenv
from pickledb import PickleDB
from swiss.match_log import MatchLog
from swiss.pairing_strategies.min_cost import pairings

load_dotenv()

ROUNDS = 3
ACTIVE = False

match_data = PickleDB('matches.db')
user_data  = PickleDB('users.db')

match_log = MatchLog()

# user_id is registered name, lowercase
def get_user(name):
    return user_data.get(name.lower())

def user_string(name):
    user = get_user(name)

    return f"{user['name']} ({user['match-wins']}-{user['match-losses']}) ({user['game-wins']}-{user['game-losses']})"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='', intents=intents)

@bot.command()
async def register(ctx, *, args):
    name = args
    user_id = name.lower()
    # check if the user is already registered
    if get_user(user_id):
        await ctx.send('ERROR: Player already registered')
        return

    if len(name) < 1 or len(name.split()) != 1:
        await ctx.send('ERROR: You need to specify a name with no spaces\ne.g. !register Elspeth')
        return

    # registration looks good, so create and store a new user dict
    new_user = {
        'id': user_id,
        'name': name,
        'results': {},
        'match-wins': 0,
        'game-wins': 0,
        'match-losses': 0,
        'game-losses': 0
    }

    user_data.set(user_id, new_user)
    user_data.save()

    await ctx.send(f'{name} has been registered. Happy dueling!')

@bot.command()
async def stats(ctx):
    await ctx.send('\n'.join(map(lambda user_id:user_string(user_id), user_data.all())))

@bot.command()
async def begin(ctx):
    global ACTIVE
    if ACTIVE:
        await ctx.send('ERROR: Draft has already begun')
        return

    user_list = user_data.all()
    random.shuffle(user_list)
    for user_id in user_list:
        match_log.add_player(user_id)

    ACTIVE = True
    await ctx.send('Pairing initiated')

@tasks.loop(seconds=5)
async def attempt_draft():
    print('Checking for new pairings')
    current_pairings = pairings(match_log)

    info = []
    for pairing in current_pairings:
        pa = pairing.player_a
        pb = pairing.player_b

        # force alphabetical for db key
        if pa > pb:
            pa = pairing.player_b
            pb = pairing.player_a

        pairing_name = pa + ' ' + pb
        match_data.set(pairing_name, {'id': pairing_name, 'pending': True})

        info.append(f'Pairing: {user_string(pa)} vs. {user_string(pb)}')

        match_log.set_player_active(pa, False)
        match_log.set_player_active(pb, False)

    match_data.save()

    print('\n'.join(info))
#    await ctx.send('\n'.join(info))

@bot.event
async def on_ready():
    print('Bot is ready!')
    attempt_draft.start()

bot.run(os.getenv('DISCORD_TOKEN'))
