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
from sqlalchemy import Column, Integer, String, ForeignKey, orm
from sqlalchemy.orm import relationship
import random

class MissionJson(object):
    def __init__(self, name, description, epilogue, xp_reward, time_required, tier, branches):
        self.name = name
        self.description = description
        self.epilogue = epilogue
        self.xp_reward = xp_reward
        self.time_required = time_required
        self.tier = tier
        self.branches = branches

class Mission(DbBase):
    """
    Hierarchecal structure that models Missions. Missions can have arbitary numbers
    of nested branches, so the class is implemented as a node in a tree.
    http://docs.sqlalchemy.org/en/latest/orm/self_referential.html
    """
    __tablename__ = 'mission'

    id = Column(Integer, primary_key = True)
    _name = Column(String)
    _description = Column(String)
    _epilogue = Column(String)
    _xp_reward = Column(Integer)
    _time_required = Column(Integer)
    _tier = Column(Integer)
    _parent_id = Column(Integer, ForeignKey('mission.id'))
    _branches = relationship('Mission')

    def __init__(self, json: MissionJson):
        self.update_data(json)

    def update_data(self, json: MissionJson):
        """
        Updates database data with the given json data.
        """
        self._name = json.name
        self._description = json.description
        self._epilogue = json.epilogue
        self._xp_reward = json.xp_reward
        self._time_required = json.time_required
        self._tier = json.tier

    @orm.reconstructor
    def init_on_load(self):
        # defaults
        self._time_progress = 0
        self._done_signal = []


    def connect_complete(self, func):
        """
        Connects a callback that will be called when
        the mission has been finished. This mission is passed as the argument.
        """
        self._done_signal.append(func)

    def run(self):
        """
        Runs a step in the Mission
        """
        self._time_progress += 1
        print('{} progress {}/{} - {}'.format(self._name, self._time_progress, self._time_required, self.get_progress_percent()))
        if self._time_progress >= self._time_required:
            # inform listeners that we're done
            for signal in self._done_signal:
                signal(self)

    def get_name(self):
        return self._name

    def get_progress_percent(self):
        """
        Gets the mission progress as a percentage
        """
        return int(self._time_progress * 100 / self._time_required)

    def get_progress_ticks(self):
        return self._time_progress

    def set_progress_ticks(self, ticks):
        self._time_progress = ticks

    def get_variable_xp_reward(self):
        """
        Gets an XP value that is +/- 10% of the base value
        """
        start = int(self._xp_reward * 0.9)
        end = int(self._xp_reward * 1.1) + 1   # + 1 since randrange excludes the end value
        return random.randrange(start, end)

    def get_info_card(self):
        """
        Gets a string that that presents all the mission data
        """
        lines = []
        lines.append('Name:         {}'.format(self._name))
        lines.append('Description:  {}'.format(self._description))
        lines.append('Tier:         {}'.format(self._tier))
        lines.append('Base XP:      {}'.format(self._xp_reward))
        lines.append('ETC:          {} seconds'.format(self._time_required))
        return '\n'.join(lines)
