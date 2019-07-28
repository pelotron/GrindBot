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

import asyncio
import config
import discord
from discord.ext import commands

_config = config.get()

def pretty_print(message):
    return '```\n{}\n```'.format(message)

async def public(bot, message):
    """Sends the message to the configured bot output channels"""
    for cid in _config.channel_ids:
        channel = bot.get_channel(cid)

        if channel is None:
            print('Unable to find channel {}.  Found:'.format(cid))
            for s in bot.servers:
                for c in s.channels:
                    print (' {} - {}'.format(c.name, c.id))
        else:
            await bot.send_message(channel, pretty_print(message))

async def private(bot, user, message):
    """Sends the message to the given user"""
    await bot.send_message(user, pretty_print(message))
