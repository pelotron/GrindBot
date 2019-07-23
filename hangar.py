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
import datetime
import json_util
from main import Session
from ship import ShipBlueprint, Ship
from sqlalchemy import orm

class Hangar():
    """
    Class that tracks and controls ship instance storage
    """

    def __init__(self):
        db = Session()
        self._ship_blueprints = db.query(ShipBlueprint).all()
        db.close()

    def update_db_ship_blueprints(self, blueprints):
        """
        Updates the DB with ship blueprints read from the ships json file
        """
        db = Session()
        for ship in blueprints:
            try:
                # update existing ships
                db_blueprint = db.query(ShipBlueprint).filter(ShipBlueprint._model == ship.model).one()
                db_blueprint.update_data(ship)
            except orm.exc.NoResultFound:
                # add new ship
                db_ship = ShipBlueprint(ship)
                db.add(db_ship)
        db.commit()
        self._ship_blueprints = db.query(ShipBlueprint).all()
        db.close()
        print('Ships loaded.')

    def get_ship_blueprints(self):
        return self._ship_blueprints

    def get_owned_ships(self, owner_id):
        db = Session()
        ships = db.query(Ship).filter(Ship._owner_id == owner_id).all()
        db.close()
        return ships

    def purchase_ship(self, owner_id, blueprint):
        # TODO - implement character wallets
        # for now just succeed
        ship = None

        if blueprint in self._ship_blueprints:
            db = Session()
            char_name = db.query(Character).filter(owner_id == Character._owner_id).one().get_name()
            ship_name = self.__generate_ship_name(char_name)
            ship = Ship(owner_id, blueprint, ship_name)
            db.add(ship)
            db.commit()
            db.close()

        return ship

    def sell_ship(self, ship):
        db = Session()
        db.delete(ship)
        # TODO - transfer money to character
        db.commit()
        db.close()

    def __generate_ship_name(self, char_name):
        """Generates a license plate-like name based on the given char name"""
        ship_name = '{}-{}'.format(
            char_name[:3].upper(),
            str(abs(hash(datetime.datetime.now())))[:3]
        )
        return ship_name

    