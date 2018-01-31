"""
This file is part of GrindBot.

GrindBot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

GrindBot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with GrindBot.  If not, see <http://www.gnu.org/licenses/>.
"""

import discord
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import json_util

# database models
import db_base
import character

config_file = 'config.json'
startup_extensions = ['grinder']

config = json_util.read_object_from_file(config_file)

bot_description = '''
bot-in-progress
 Building a semi-idle RPG.

'''

bot = commands.Bot(command_prefix = '!', description = bot_description)

db_engine = create_engine('sqlite:///%s' % config.db_file, echo = False)
db_base.DbBase.metadata.create_all(db_engine, checkfirst = True)

Session = sessionmaker(bind = db_engine)
Session.configure(bind = db_engine)

def is_admin(ctx):
    ids = [a['id'] for a in config.admins]
    return ctx.message.author.id in ids

@bot.event
async def on_ready():
    print('Logged in as %s, id %s' % (bot.user.name, bot.user.id))

@bot.command()
@commands.check(is_admin)
async def shutdown():
    """Shuts down the bot."""
    print('Shutting down Discord bot.')
    await bot.close()

@bot.command()
@commands.check(is_admin)
async def load(extension_name : str):
    """Loads an extension."""
    try:
        bot.load_extension(extension_name)
    except (AttributeError, ImportError) as e:
        await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        return
    await bot.say("{} loaded.".format(extension_name))

@bot.command()
@commands.check(is_admin)
async def unload(extension_name : str):
    """Unloads an extension."""
    bot.unload_extension(extension_name)
    await bot.say("{} unloaded.".format(extension_name))

@bot.command()
async def admins():
    """Print the list of admins."""
    # print admins
    adminnames = [a['name'] for a in config.admins]
    adminstring = '\n'.join(['%s'] * len(adminnames)) % tuple(adminnames)
    await bot.say(adminstring)

# start up
if __name__ == '__main__':
    for extension in startup_extensions:
        bot.load_extension(extension)

    bot.run(config.token)
