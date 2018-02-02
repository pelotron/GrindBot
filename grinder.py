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
import datetime
import discord
from discord.ext import commands

from character import Character
from main import Session
from main import config
from main import config_file
from main import is_admin
import discord_output
import json_util

class Grinder():
    """
    Class that runs HeroGrinder game logic.
    Implemented as a Discord bot cog.
    """

    def __init__(self, bot):
        self.bot = bot
        self.characters = {}
        self.game_uptime = 0

        self.db = Session()
        characters = self.db.query(Character).all()
        for c in characters:
            # load character handles
            c.connect_level_up(self.announce_character_level)
            self.characters[c.owner_id] = c
            print('Loaded %s' % c)

        self.game_task = self.bot.loop.create_task(self.game_loop())

    def __unload(self):
        """Called when this cog is unloaded on shutdown."""
        print('Shutting down Grinder.')
        self.game_task.cancel()
        self.db.commit()
        self.db.close()

    async def announce_character_level(self, character):
        """Callback bound to characters that prints a level-up announcement."""
        await discord_output.public(self.bot, '%s is now level %s!' % (character.name, character.level))

    @commands.command(pass_context = True)
    async def create_character(self, ctx, *args):
        """Creates a new character for the player if they don't have one"""
        player = ctx.message.author.id
        if player in self.characters.keys():
            await self.bot.say('You already have a character named %s.' % self.characters[player].name)
        elif len(args) == 0:
            await self.bot.say('You must name your character.')
        else:
            name = args[0]
            # create the new char and store in the db
            c = Character(name, player)
            c.connect_level_up(self.announce_character_level)
            self.characters[player] = c
            self.db.add(c)
            self.db.commit()
            await self.bot.say('Created character %s!' % name)

    @commands.command(pass_context = True)
    async def delete_character(self, ctx):
        """Delete's a player's character"""
        player = ctx.message.author.id
        if player in self.characters.keys():
            c = self.characters[player]
            self.db.delete(c)
            self.db.commit()
            name = c.name
            del self.characters[player]
            await self.bot.say('%s has died.' % name)
        else:
            await self.bot.say('You do not have a live character.')

    @commands.command(pass_context = True)
    async def progress(self, ctx):
        """Reports a player's progress."""
        player = ctx.message.author.id
        if player in self.characters.keys():
            c = self.characters[player]
            await self.bot.say(c.get_progress())
        else:
            await self.bot.say('Create a character first.')

    @commands.command(pass_context = True)
    @commands.check(is_admin)
    async def db_commit_wait(self, ctx, *args):
        """[ADMIN] Gets/sets the number of game ticks between database commits."""
        if len(args) == 0:
            await self.bot.say('DB commit wait is %s ticks.' % config.db_commit_wait)
        else:
            config.db_commit_wait = args[0]
            json_util.write_object_to_file(config_file, config)
            await self.bot.say('DB commit wait set to %s ticks.' % args[0])

    @commands.command()
    async def uptime(self):
        """Gets Grinder's uptime."""
        msg = str(datetime.timedelta(seconds = self.game_uptime))
        await self.bot.say('Grinder has been running for %s.' % msg)

    async def game_loop(self):
        """Main game loop."""
        await self.bot.wait_until_ready()
        print('Game loop started.')

        while True:
            # hopefully we are here when the task gets canceled...
            await asyncio.sleep(1)

            self.game_uptime += 1
            for c in self.characters.values():
                await c.add_xp(1)

            if self.game_uptime % int(config.db_commit_wait) == 0:
                self.db.commit()

def setup(bot):
    bot.add_cog(Grinder(bot))
    print('Added Grinder')
