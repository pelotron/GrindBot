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

from cargo import Cargo
from database import DbModel
from module import Module
from module import ModuleType
from sqlalchemy import Column, Integer, String, ForeignKey, orm
from sqlalchemy.orm import relationship

class WeaponJson(object):
    def __init__(self, name, description, base_damage_dice):
        self.name = name
        self.description = description
        self.base_damage_dice = base_damage_dice

class WeaponBlueprint(DbModel):
    """
    Unique weapon blueprint
    """
    __tablename__ = 'weapon_blueprint'
    id = Column(Integer, primary_key = True)
    _name = Column(String)
    _description = Column(String)
    _base_damage_dice = Column(String)

    def __init__(self, json: WeaponJson):
        self.update_data(json)

    def update_data(self, json: WeaponJson):
        self._name = json.name
        self._description = json.description
        self._base_damage_dice = json.base_damage_dice

class Weapon(Cargo, Module):
    """
    Class for instances of weapons
    """
    __tablename__ = 'weapon'

    id = Column(Integer, ForeignKey('cargo.id'), primary_key = True)
    _bonus_damage = Column(Integer)
    _blueprint_id = Column(Integer, ForeignKey('weapon_blueprint.id'))
    _blueprint = relationship('WeaponBlueprint', lazy = 'joined')

    __mapper_args__ = {
        'polymorphic_identity':'weapon',
    }

    def __init__(self, blueprint):
        self._module_type = ModuleType.WEAPON
        self._blueprint = blueprint
