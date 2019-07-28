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
import config
from database import db
from hangar import Hangar
from main import is_admin
import discord_output
import json_util
import mission
from mission_control import MissionControl

# it would be nice for Grinder to own its own instance of this,
# but it seems that this must be static since command checks can't use instance methods
_characters = {}

# command check that enforces character existence
def has_character(ctx):
    return ctx.message.author.id in _characters.keys()

class Grinder():
    """
    Class that runs HeroGrinder game logic.
    Implemented as a Discord bot cog.

    """

    def __init__(self, bot):
        self._bot = bot
        _characters = {}
        self._game_uptime = 0
        self._config = config.get()

        # message queues
        self._public_messages = []
        self._private_messages = {} # user: list(messages)

        ships = json_util.read_object_from_file('ships.json')
        self._hangar = Hangar()
        self._hangar.update_db_ship_blueprints(ships)

        random.seed()

        # pick up mission updates
        self._mission_control = MissionControl()
        self._mission_control.update_db_missions()
        print('Missions loaded.')

        self.__init_characters()

        self._game_task = self._bot.loop.create_task(self.__game_loop())

    def __unload(self):
        """Called when this cog is unloaded on shutdown."""
        print('Shutting down Grinder.')
        self._game_task.cancel()
        self.__save_game_to_db()

    def __init_characters(self):
        characters = db.query(Character).all()
        for c in characters:
            db.expunge(c) # detach object from db
            self.__init_character(c)
            print('Loaded {}'.format(c))

    def __init_character(self, character):
        character.connect_level_up(self.__announce_character_level)
        character.connect_mission_complete(self.__mission_complete)
        _characters[character._owner_id] = character

    @commands.command(pass_context = True)
    async def create_character(self, ctx, *args):
        """Creates a new character for the player if they don't have one"""
        player = ctx.message.author.id
        msg = ''

        if player in _characters:
            msg = 'You already have a character named {}.'.format(_characters[player]._name)
        elif len(args) == 0:
            msg = 'You must name your character.'
        elif len(args[0]) > 30:
            msg = 'Don\'t be a troll. Think of a name with a max of 30 characters.'
        else:
            name = args[0]
            # create the new char and store in the db
            c = Character(name, player)
            db.add(c)
            db.commit()
            db.expunge(c)

            self.__init_character(c)
            msg = 'Created character {}!'.format(name)
            self._public_messages.append('{} has entered the world!'.format(name))

        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    async def delete_character(self, ctx):
        """Delete's a player's character"""
        player = ctx.message.author.id
        msg = ''
        if player in _characters:
            c = _characters[player]
            db.delete(c)
            db.commit()
            name = c._name
            del _characters[player]
            msg = '{} has been deleted.'.format(name)
            self._public_messages.append('{} stumbled out an airlock and died.'.format(name))
        else:
            msg = 'You do not have a live character.'

        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    async def char(self, ctx):
        """Gets your current character sheet."""
        player = ctx.message.author.id
        msg = ''
        if player in _characters:
            c = _characters[player]
            msg = c.get_info_card()
        else:
            msg = 'Create a character first.'

        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    @commands.check(is_admin)
    async def db_commit_wait(self, ctx, *args):
        """[ADMIN] Gets/sets the number of game ticks between database commits."""
        msg = ''
        if len(args) == 0:
            msg = 'DB commit wait is {} ticks.'.format(self._config.db_commit_wait)
        else:
            self._config.db_commit_wait = args[0]
            config.write(self._config)
            msg = 'DB commit wait set to {} ticks.'.format(self._config.db_commit_wait)

        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    async def uptime(self, ctx):
        """Gets Grinder's uptime."""
        time = str(datetime.timedelta(seconds = self._game_uptime))
        msg = 'Grinder has been running for {}.'.format(time)
        await discord_output.private(self._bot, ctx.message.author, msg)

    @commands.command(pass_context = True)
    @commands.check(has_character)
    async def ship(self, ctx, *args):
        """
        Interact with your current ship.
        usages:
         !ship
         !ship list
         !ship name (ship name)
         !ship board (ship name)
         !ship buy (model name)
         !ship sell (ship name)
        """

        msg = 'Sorry, command not understood... try !help ship'
        owner_id = ctx.message.author.id
        character = _characters[owner_id]
        current_ship = character.get_current_ship()

        if len(args) == 0:
            msg = 'You are not aboard a ship.'
            if current_ship is not None:
                name = current_ship.get_name()
                msg = 'You are aboard {}.\n\n{}'.format(
                    name if name is not None else 'an unnamed ship (you can name it with !ship name [name])', current_ship.get_info_card())
        else:
            if args[0] == 'list':
                ships = self._hangar.get_owned_ships(character)
                if len(ships) == 0:
                    msg = 'You don\'t own any ships.'
                else:
                    msg = 'Your ships:\n\n'
                    msg += '\n\n'.join(s.get_info_card() for s in ships)
            elif args[0] == 'name':
                msg = 'You must board a ship before naming it.'
                if len(args) >= 2 and current_ship is not None:
                    current_ship.set_name(args[1])
                    msg = 'You have christened this ship \'{}\'.'.format(args[1])
                    current_ship.save(db)
                    db.commit()
            elif args[0] == 'board':
                msg = 'Specify a ship\'s name to board.'
                if len(args) >= 2:
                    ships = self._hangar.get_owned_ships(character)
                    for s in ships:
                        if s.get_name().lower() == args[1].lower():
                            character.set_current_ship(s)
                            msg = 'You boarded {}.'.format(s.get_name())
                            break
            elif args[0] == 'buy':
                ships = self._hangar.get_ship_blueprints()
                if len(args) == 1:
                    # just return the list of ships
                    msg = 'Ships available to buy at this hangar:\n\n'
                    msg += '\n\n'.join(s.get_info_card() for s in ships)
                else:
                    subcmd = args[1].lower()
                    blueprint = [s for s in ships if s.get_model().lower() == subcmd]
                    if len(blueprint) == 1:
                        bp = blueprint[0]
                        if character.can_afford(bp.get_cost()):
                            new_ship = self._hangar.purchase_ship(character, bp)
                            if new_ship is not None:
                                # auto-board for now
                                character.set_current_ship(new_ship)
                                msg = 'You successfully bought and boarded a {}!'.format(new_ship.get_model())
                                self._public_messages.append('{} just purchased a ship!  (Model: {})'.format(
                                    character.get_name(), new_ship.get_model()))
                        else:
                            msg = 'Sorry, you need {} more credits to purchase the {}.'.format(
                                bp.get_cost() - character.get_credits(),
                                bp.get_model()
                            )
            elif args[0] == 'sell':
                msg = 'Specify a ship\'s name to sell.'
                if len(args) >= 2:
                    ships = self._hangar.get_owned_ships(character)
                    for s in ships:
                        if s.get_name().lower() == args[1].lower():
                            if current_ship is not None and s.id == current_ship.id:
                                character.set_current_ship(None)
                            self._hangar.sell_ship(character, s)
                            msg = 'You sold {}!'.format(s.get_name())
                            self._public_messages.append('{} sold their ship \'{}\'!  (Model: {})'.format(
                                character.get_name(), s.get_name(), s.get_model()))

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

        for c in _characters.values():
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

        for c in sorted(_characters.values(), key = lambda char: char.get_xp(), reverse = True):
            msg += layout.format(c.get_level(), c._name, c.get_xp(), l = levellen, n = namelen, x = xplen)

        await discord_output.private(self._bot, ctx.message.author, msg)

    def __announce_character_level(self, character):
        """Callback bound to characters that queues a level-up announcement."""
        msg = '{} is now level {} ({} XP)!'.format(character._name, character.get_level(), character.get_xp())
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
        new_mission = self._mission_control.generate_mission_for(character)

        prev_mission = character.get_current_mission()
        aux_msg = ''
        if prev_mission is not None and prev_mission.id == new_mission.id:
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
        for c in _characters.values():
            c.save(db)
        db.commit()

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
            for c in _characters.values():
                if c.get_current_mission() is None:
                    self.__start_next_mission(c)
                else:
                    c.run_current_mission()

            if self._game_uptime % int(self._config.db_commit_wait) == 0:
                print('saving game state')
                self.__save_game_to_db()

def setup(bot):
    """Cog setup"""
    bot.add_cog(Grinder(bot))
    print('Added Grinder')
