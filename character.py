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

from db_base import DbBase
from sqlalchemy import Column, Integer, String, orm

def get_level(xp):
    level = int((xp / float(100)) ** (1/1.5)) + 1
    return level;

class Character(DbBase):
    __tablename__ = 'character'

    id = Column(Integer, primary_key = True)
    name = Column(String)
    xp = Column(Integer)
    owner_id = Column(String)

    def __init__(self, name, owner_id):
        self.name = name
        self.owner_id = owner_id
        self.xp = 0
        self.level = 0
        self.signal_level_up = None

    @orm.reconstructor
    def init_on_load(self):
        self.level = get_level(self.xp)

    def __repr__(self):
        return '<Character(name = %s, xp = %d, owner_id = %s)>' % (
            self.name, self.xp, self.owner_id)

    def add_xp(self, xp):
        """Adds xp to this character."""
        self.xp += xp
        level = get_level(self.xp)

        if level > self.level:
            # account for possible multi-level-up
            for i in range(self.level, level):
                self.level += 1
                if self.signal_level_up is not None:
                    self.signal_level_up(self)

    def connect_level_up(self, func):
        """
        Connects an async callback that will be called when this character
        gains a level. This character is passed as the argument.
        """
        self.signal_level_up = func

    def get_progress(self):
        """Gets a string summarizing the character's state."""
        return '%s is level %d with %d xp.' % (self.name, get_level(self.xp), self.xp)
