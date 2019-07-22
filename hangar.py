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
        return ships

    def purchase_ship(self, owner_id, blueprint):
        # TODO - implement character wallets
        # for now just succeed
        ship = None

        if blueprint in self._ship_blueprints:
            ship = Ship(owner_id, blueprint)
            db = Session()
            db.add(ship)
            db.commit()
            db.close()

        return ship
    