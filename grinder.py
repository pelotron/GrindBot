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

# external modules
import asyncio
import datetime
import discord
from discord.ext import commands
import random

# Grinder modules
from character import Character
from main import Session, config, config_file, is_admin
import discord_output
import json_util
import mission
from mission_control import MissionControl

class Grinder():
    """
    Class that runs HeroGrinder game logic.
    Implemented as a Discord bot cog.
    """

    def __init__(self, bot):
        self._bot = bot
        self._characters = {}
        self._game_uptime = 0

        # message queues
        self._public_messages = []
        self._private_messages = {} # user: list(messages)

        random.seed()
        db = Session()

        # pick up mission updates
        self._mission_control = MissionControl()
        self._mission_control.update_db_missions(db)
        db.commit()
        print('Missions loaded.')

        self.__init_characters(db)

        db.close()

        self._game_task = self._bot.loop.create_task(self.__game_loop())

    def __unload(self):
        """Called when this cog is unloaded on shutdown."""
        print('Shutting down Grinder.')
        self._game_task.cancel()
        self.__save_game_to_db()

    def __init_characters(self, db):
        characters = db.query(Character).all()
        for c in characters:
            db.expunge(c) # detach object from db
            self.__init_character(c)
            print('Loaded %s' % c)

    def __init_character(self, character):
        character.connect_level_up(self.__announce_character_level)
        character.connect_mission_complete(self.__mission_complete)
        self._characters[character._owner_id] = character

    @commands.command(pass_context = True)
    async def create_character(self, ctx, *args):
        """Creates a new character for the player if they don't have one"""
        player = ctx.message.author.id
        msg = ''

        if player in self._characters:
            msg = 'You already have a character named %s.' % self._characters[player]._name
        elif len(args) == 0:
            msg = 'You must name your character.'
        elif len(args[0]) > 30:
            msg = 'Don\'t be a troll. Think of a name with a max of 30 characters.'
        else:
            name = args[0]
            # create the new char and store in the db
            c = Character(name, player)

            db = Session()
            db.add(c)
            db.commit()
            db.expunge(c)
            db.close()

            self.__init_character(c)
            msg = 'Created character %s!' % name
            self._public_messages.append('%s has entered the world!' % name)

        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    async def delete_character(self, ctx):
        """Delete's a player's character"""
        player = ctx.message.author.id
        msg = ''
        if player in self._characters:
            c = self._characters[player]
            db = Session()
            db.delete(c)
            db.commit()
            db.close()
            name = c._name
            del self._characters[player]
            msg = '%s has been deleted.' % name
            self._public_messages.append('%s stumbled out an airlock and died.' % name)
        else:
            msg = 'You do not have a live character.'

        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    async def progress(self, ctx):
        """Reports a player's progress."""
        player = ctx.message.author.id
        msg = ''
        if player in self._characters:
            c = self._characters[player]
            msg = c.get_progress()
        else:
            msg = 'Create a character first.'

        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    @commands.check(is_admin)
    async def db_commit_wait(self, ctx, *args):
        """[ADMIN] Gets/sets the number of game ticks between database commits."""
        msg = ''
        if len(args) == 0:
            msg = 'DB commit wait is %s ticks.' % config.db_commit_wait
        else:
            config.db_commit_wait = args[0]
            json_util.write_object_to_file(config_file, config)
            msg = 'DB commit wait set to %s ticks.' % config.db_commit_wait

        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    async def uptime(self, ctx):
        """Gets Grinder's uptime."""
        time = str(datetime.timedelta(seconds = self._game_uptime))
        msg = 'Grinder has been running for %s.' % time
        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    async def scoreboard(self, ctx):
        """Prints a scoreboard of all characters."""
        namestr = 'Name'
        xpstr = 'XP'
        levelstr = 'Level'

        namelen = len(namestr)
        xplen = len(xpstr)
        levellen = len(levelstr)

        for c in self._characters.values():
            if len(c._name) > namelen:
                namelen = len(c._name)
            if len(str(c.get_xp())) > xplen:
                xplen = len(str(c.get_xp()))
            if (len(str(c.get_level())) > levellen):
                levellen = len(str(c.get_level()))

        levellen += 1
        namelen += 2
        xplen += 1

        layout = "{0:>{l}} | {1:^{n}} | {2:<{x}}\n"
        msg = layout.format(levelstr, namestr, xpstr, l = levellen, n = namelen, x = xplen)
        msg += '-' * (levellen + namelen + xplen + 6)
        msg += '\n'

        for c in sorted(self._characters.values(), key = lambda char: char.get_xp(), reverse = True):
            msg += layout.format(c.get_level(), c._name, c.get_xp(), l = levellen, n = namelen, x = xplen)

        await discord_output.private(self._bot, ctx.message.author, msg)

    def __announce_character_level(self, character):
        """Callback bound to characters that queues a level-up announcement."""
        msg = '%s is now level %s (%d XP)!' % (character._name, character.get_level(), character.get_xp())
        self._public_messages.append(msg)

    def __mission_complete(self, character):
        """Callback bound to character mission complete signals"""
        current_mission = character.get_current_mission()
        xp_gain = current_mission.get_variable_xp_reward()
        character.add_xp(xp_gain)
        self.__queue_private_message(character._owner_id, current_mission._epilogue)
        self.__queue_private_message(character._owner_id, 'You completed {} and were awarded {} XP!'.format(current_mission._name, xp_gain))
        self.__start_next_mission(character)

    def __start_next_mission(self, character):
        db = Session()
        new_mission = self._mission_control.generate_mission_for(character, db)
        db.close()

        prev_mission = character.get_current_mission()
        aux_msg = ''
        if prev_mission.id == new_mission.id:
            aux_msg = 'Deja vu...\n'
        character.set_new_mission(new_mission)
        self.__queue_private_message(character._owner_id, 'You have started a new mission.\n{}\n{}'.format(aux_msg, new_mission.get_info_card()))

    async def __print_message_queues(self):
        """Prints all pending game loop messages."""
        if self._public_messages:
            concat = '\n'.join(self._public_messages)
            self._public_messages = []
            await discord_output.public(self._bot, concat)

        if self._private_messages:
            for user_id in self._private_messages:
                concat = '\n'.join(self._private_messages[user_id])
                user = await self._bot.get_user_info(user_id)
                await discord_output.private(self._bot, user, concat)
            self._private_messages = {}

    def __save_game_to_db(self):
        db = Session()
        for c in self._characters.values():
            c.save(db)
        db.commit()
        db.close()

    def __queue_private_message(self, user, message):
        if user not in self._private_messages:
            self._private_messages[user] = []
        self._private_messages[user].append(message)

    async def __game_loop(self):
        """Main game loop."""
        await self._bot.wait_until_ready()
        print('Game loop started.')

        while True:
            await self.__print_message_queues()
            await asyncio.sleep(1)

            # synchronous logic only below
            self._game_uptime += 1
            for c in self._characters.values():
                if c.get_current_mission() is None:
                    self.__start_next_mission(c)
                else:
                    c.run_current_mission()

            if self._game_uptime % int(config.db_commit_wait) == 0:
                print('saving game state')
                self.__save_game_to_db()

def setup(bot):
    """Cog setup"""
    bot.add_cog(Grinder(bot))
    print('Added Grinder')
