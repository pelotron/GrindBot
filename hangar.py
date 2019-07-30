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

from character import Character
import database
import datetime
import json_util
from ship import ShipBlueprint, Ship
from sqlalchemy import orm

class Hangar():
    """
    Class that tracks and controls ship instance storage
    """

    def __init__(self):
        self._ship_blueprints = database.session.query(ShipBlueprint).all()

    def update_db_ship_blueprints(self, blueprints):
        """
        Updates the DB with ship blueprints read from the ships json file
        """
        for ship in blueprints:
            try:
                # update existing ships
                db_blueprint = database.session.query(ShipBlueprint).filter(ShipBlueprint._model == ship.model).one()
                db_blueprint.update_data(ship)
            except orm.exc.NoResultFound:
                # add new ship
                db_ship = ShipBlueprint(ship)
                database.session.add(db_ship)
        database.session.commit()
        self._ship_blueprints = database.session.query(ShipBlueprint).all()
        print('Ships loaded.')

    def get_ship_blueprints(self):
        return self._ship_blueprints

    def get_owned_ships(self, character):
        ships = database.session.query(Ship).filter(Ship._owner_id == character.id).all()
        return ships

    def purchase_ship(self, character, blueprint):
        ship = None

        if blueprint in self._ship_blueprints:
            character.subtract_credits(blueprint.get_cost())
            ship_name = self.__generate_ship_name(character)
            ship = Ship(character.id, blueprint, ship_name)
            database.session.add(ship)
            database.session.commit()

        return ship

    def sell_ship(self, character, ship):
        character.add_credits(ship.get_cost())
        database.session.delete(ship)
        database.session.commit()

    def __generate_ship_name(self, character):
        """Generates a license plate-like name based on the given character"""
        ship_name = '{}-{}'.format(
            character.get_name()[:3].upper(),
            str(abs(hash(datetime.datetime.now())))[:3]
        )
        return ship_name

    