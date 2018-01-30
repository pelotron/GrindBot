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
import discord
from discord.ext import commands

from character import Character
from main import Session

class Grinder():
    """
    Class that runs HeroGrinder game logic.
    Implemented as a Discord bot cog.
    """

    def __init__(self, bot):
        self.bot = bot
        self.characters = {}
        self.db = Session()
        characters = self.db.query(Character).all()
        for c in characters:
            # load into memory
            self.characters[c.owner_id] = c
            print(c)

        self.running = True
        self.loop_task = self.bot.loop.create_task(self.game_loop())

    # called when this cog is unloaded (shutdown)
    def __unload(self):
        print('Shutting down Grinder.')
        self.running = False

        # hack! need to figure out a way to end the task synchronously if possible
        self.loop_task.cancel()

        for c in self.characters.values():
            self.db.add(c)
        self.db.commit()
        self.db.close()

    @commands.command(pass_context = True)
    async def create_character(self, ctx, *args):
        """Creates a new character for the player if they don't have one"""
        player = ctx.message.author.id
        if player in self.characters.keys():
            await self.bot.say('You already have a character named %s.' % self.characters[player].name)
        elif len(args) == 0:
            await self.bot.say('You must name your character.')
        else:
            # create the new char and store in the db
            c = Character()
            c.name = args[0]
            c.owner_id = player
            c.uptime = 0
            self.characters[player] = c
            self.db.add(c)
            self.db.commit()
            await self.bot.say('Created character %s!' % args[0])

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
            await self.bot.say('%s has been alive for %d seconds.' % (c.name, c.uptime))
        else:
            await self.bot.say('Create a character first.')

    async def game_loop(self):
        """Main game loop."""
        await self.bot.wait_until_ready()
        print('Game loop started.')
        while self.running:
            await asyncio.sleep(1) # 1 Hz
            for c in self.characters.values():
                c.uptime += 1
            self.db.commit()
        print('Game loop ended.')

def setup(bot):
    bot.add_cog(Grinder(bot))
