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

from database import DbModel
from sqlalchemy import Column, Integer, String, ForeignKey, orm
from sqlalchemy.orm import relationship

from mission import Mission

def calc_level(xp):
    level = int((xp / float(100)) ** (1/1.5)) + 1
    return level

class Character(DbModel):
    __tablename__ = 'character'

    id = Column(Integer, primary_key = True)
    _name = Column(String)
    _owner_id = Column(String) # Discord User ID
    _xp = Column(Integer)
    _tier = Column(Integer)
    _credits = Column(Integer)
    _current_mission_id = Column(Integer, ForeignKey('mission.id'))
    _current_mission = relationship('Mission')
    _current_mission_ticks = Column(Integer)
    _current_ship_id = Column(Integer, ForeignKey('ship.id'))
    _current_ship = relationship('Ship', lazy='joined')

    def __init__(self, name, owner_id):
        self._name = name
        self._owner_id = owner_id
        self._tier = 1
        self._xp = 0
        self._level = 0
        self._credits = 250000 # this may need to be a config value
        self._current_mission_ticks = 0
        self._current_mission = None
        self._current_ship = None
        self._signal_level_up = []
        self._signal_mission_complete = []

    @orm.reconstructor
    def init_on_load(self):
        self._level = calc_level(self._xp)
        self._signal_level_up = []
        self._signal_mission_complete = []
        if self._current_mission_id is None:
            self._current_mission = None
        else:
            self._current_mission.set_progress_ticks(self._current_mission_ticks)
            self._current_mission.connect_complete(self.__mission_complete)

    def __repr__(self):
        return '<Character(name = {}, xp = {}, owner_id = {})>'.format(
            self._name, self._xp, self._owner_id)

    def add_xp(self, xp):
        """Adds xp to this character."""
        self._xp += xp
        level = calc_level(self._xp)

        if level > self._level:
            # account for possible multi-level-up
            for _ in range(self._level, level):
                self._level += 1
                for signal in self._signal_level_up:
                    signal(self)

    def connect_level_up(self, func):
        """
        Connects a callback that will be called when this character
        gains a level. This character is passed as the argument.
        """
        self._signal_level_up.append(func)

    def connect_mission_complete(self, func):
        """
        Connects a callback that will be called when this character
        completes its current mission. This character is passed as the argument.
        """
        self._signal_mission_complete.append(func)

    def get_level(self):
        return self._level

    def get_xp(self):
        return self._xp

    def get_name(self):
        return self._name

    def set_new_mission(self, mission):
        self._current_mission_id = mission.id
        self._current_mission = mission
        self._current_mission_ticks = 0
        mission.connect_complete(self.__mission_complete)

    def set_current_ship(self, ship):
        self._current_ship_id = None if ship is None else ship.id
        self._current_ship = ship

    def get_current_ship(self):
        return self._current_ship

    def run_current_mission(self):
        self._current_mission.run()

    def get_current_mission(self):
        return self._current_mission

    def can_afford(self, amount):
        return self._credits >= amount

    def get_credits(self):
        return self._credits

    def subtract_credits(self, amount):
        if self.can_afford(amount):
            self._credits -= amount
        else:
            raise Exception('{} has {} and can\'t pay {}. Call can_afford()'.format(
                self._name, self._credits, amount))

    def add_credits(self, amount):
        self._credits += amount

    def get_info_card(self):
        lines = []
        lines.append('Name:             {}'.format(self._name))
        lines.append('Level:            {}'.format(self._level))
        lines.append('XP:               {}'.format(self._xp))
        lines.append('Credits:          {}'.format(self._credits))
        m = self._current_mission
        lines.append('Current mission:  {} ({}%)'.format(m.get_name(), m.get_progress_percent()))
        if self._current_ship is not None:
            lines.append('Currently aboard your ship \'{}\''.format(self._current_ship.get_name()))
        return '\n'.join(lines)

    def save(self, db):
        self._current_mission_ticks = self._current_mission.get_progress_ticks()
        super().save(db)

    def __mission_complete(self, mission):
        for signal in self._signal_mission_complete:
            signal(self)
