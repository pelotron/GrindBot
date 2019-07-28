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

import character
from database import db
import json_util
from mission import Mission
import random
from sqlalchemy import orm

class MissionControl():
    """
    Class that tracks and controls mission behavior
    """

    def __init__(self):
        self._mission_tree = json_util.read_object_from_file('missions.json')

    def update_db_missions(self):
        """
        Updates the DB with missions read from the missions json file
        """
        self.__update_db_missions(self._mission_tree)
        db.commit()

    def generate_mission_for(self, character):
        """
        Generates a mission for the given character.
        """
        print('generating mission')
        current_mission = character.get_current_mission()
        mission_choices = []

        if current_mission is not None:
            # Choose from branching missions if any
            mission_choices = db.query(Mission).filter(Mission._parent_id == current_mission.id).all()

        if len(mission_choices) == 0:
            # Choose from root missions
            mission_choices = db.query(Mission).filter(Mission._parent_id == None).all()
        
        print('queried {} missions'.format(len(mission_choices)))

        new_mission = self.__choose_mission_from(mission_choices)
        db.expunge(new_mission)
        print('got mission {}'.format(new_mission._name))

        return new_mission

    def __update_db_missions(self, mission_tree):
        """
        Postorder traversal of a list of MissionJson objects that converts them into
        missions that are stored in the DB.  Recursive.
        """
        parent_dbm_list = []

        for mission in mission_tree:
            # recurse down to leaf nodes
            child_dbm_list = self.__update_db_missions(mission.branches)

            db_mission = None

            try:
                # update existing missions
                db_mission = db.query(Mission).filter(Mission._name == mission.name).one()
                db_mission.update_data(mission)
            except orm.exc.NoResultFound:
                # add new mission
                db_mission = Mission(mission)
                db.add(db_mission)

            db_mission._branches = child_dbm_list
            parent_dbm_list.append(db_mission)

        return parent_dbm_list

    def __choose_mission_from(self, mission_list):
        # for now just get a random one
        return random.choice(mission_list)
