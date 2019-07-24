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

import config
import discord_output
import json_util

# database models
import db_base
import character
import ship

startup_extensions = ['grinder']

config = config.get()

bot_description = '''
bot-in-progress
 Building a semi-idle RPG.

'''

bot = commands.Bot(command_prefix = '!', description = bot_description, pm_help = True)

db_engine = create_engine('sqlite:///%s' % config.db_file, echo = False)
db_base.DbBase.metadata.create_all(db_engine, checkfirst = True)

Session = sessionmaker(bind = db_engine, expire_on_commit = False)

def is_admin(ctx):
    ids = [a['id'] for a in config.admins]
    return ctx.message.author.id in ids

@bot.event
async def on_ready():
    print('Logged in as %s, id %s' % (bot.user.name, bot.user.id))

@bot.command()
@commands.check(is_admin)
async def shutdown():
    """[ADMIN] Shuts down the bot."""
    print('Shutting down Discord bot.')
    await bot.close()

@bot.command(pass_context = True)
@commands.check(is_admin)
async def load(ctx, extension_name : str):
    """[ADMIN] Loads an extension."""
    try:
        bot.load_extension(extension_name)
    except (AttributeError, ImportError) as e:
        msg = '```py\n{}: {}\n```'.format(type(e).__name__, str(e))
        await discord_output.private(bot, ctx.message.author, msg)
        return
    msg = '{} loaded.'.format(extension_name)
    await discord_output.private(bot, ctx.message.author, msg)

@bot.command(pass_context = True)
@commands.check(is_admin)
async def unload(ctx, extension_name : str):
    """[ADMIN] Unloads an extension."""
    bot.unload_extension(extension_name)
    msg = '{} unloaded.'.format(extension_name)
    await discord_output.private(bot, ctx.message.author, msg)

@bot.command(pass_context = True)
async def admins(ctx):
    """Print the list of admins."""
    adminnames = [a['name'] for a in config.admins]
    adminstring = '\n'.join(adminnames)
    await discord_output.private(bot, ctx.message.author, adminstring)

# start up
if __name__ == '__main__':
    for extension in startup_extensions:
        bot.load_extension(extension)

    try:
        bot.run(config.token)
    except Exception as e:
        print('Exception while running bot:')
        print(e)
