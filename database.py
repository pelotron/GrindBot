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

import config
from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base

DbModel = declarative_base()

# Database models
from character import Character
from mission import Mission
from ship import Ship
from weapon import WeaponBlueprint

_config = config.get()

def _save(self, session):
    session.merge(self)

DbModel.save = _save

# init
_db_engine = create_engine('sqlite:///{}'.format(_config.db_file), echo = False)
DbModel.metadata.create_all(_db_engine, checkfirst = True)

Session = orm.sessionmaker(bind = _db_engine, expire_on_commit = False)

# global DB
session = Session()

def update_db_weapon_blueprints(weapons):
    """
    Updates the DB with weapon blueprints read from the weapons json file
    """
    for weapon in weapons:
        try:
            # update existing weapons
            db_blueprint = session.query(WeaponBlueprint).filter(WeaponBlueprint._name == weapon.name).one()
            db_blueprint.update_data(weapon)
        except orm.exc.NoResultFound:
            # add new ship
            db_weapon = WeaponBlueprint(weapon)
            session.add(db_weapon)
    session.commit()
    print('Weapons loaded.')
    