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
from flight_status import FlightStatus
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

class ShipJson(object):
    def __init__(self, model, cost, mass, cargo_capacity, fuel_capacity, weapon_hardpoints, aux_hardpoints, description):
        self.model = model
        self.cost = cost
        self.mass = mass
        self.cargo_capacity = cargo_capacity
        self.fuel_capacity = fuel_capacity
        self.weapon_hardpoints = weapon_hardpoints
        self.aux_hardpoints = aux_hardpoints
        self.description = description

class ShipBlueprint(DbBase):
    """
    Class that models a ship type blueprint
    """
    __tablename__ = 'ship_blueprint'

    id = Column(Integer, primary_key = True)
    _model = Column(String)
    _cost = Column(Integer)
    _mass = Column(Integer)
    _cargo_capacity = Column(Integer)
    _fuel_capacity = Column(Integer)
    _weapon_hardpoints = Column(Integer)
    _aux_hardpoints = Column(Integer)
    _description = Column(String)

    def __init__(self, json: ShipJson):
        self.update_data(json)

    def update_data(self, json: ShipJson):
        self._model = json.model
        self._cost = json.cost
        self._mass = json.mass
        self._cargo_capacity = json.cargo_capacity
        self._fuel_capacity = json.fuel_capacity
        self._weapon_hardpoints = json.weapon_hardpoints
        self._aux_hardpoints = json.aux_hardpoints
        self._description = json.description

    def get_cost(self):
        return self._cost

    def get_model(self):
        return self._model

    def get_info_card(self):
        lines = []
        lines.append('Model:                    {}'.format(self._model))
        lines.append('Cost:                     {}'.format(self._cost))
        lines.append('Mass:                     {} t'.format(self._mass))
        lines.append('Cargo capacity:           {} t'.format(self._cargo_capacity))
        lines.append('Fuel capacity:            {} t'.format(self._fuel_capacity))
        lines.append('Weapon hardpoints:        {}'.format(self._weapon_hardpoints))
        lines.append('Auxilliary hardpoints:    {}'.format(self._aux_hardpoints))
        return '\n'.join(lines)

class Ship(DbBase):
    """
    Class that models an instance of ship the player can own/fly
    """
    __tablename__ = 'ship'

    id = Column(Integer, primary_key = True)
    _owner_id = Column(String) # Character ID
    _name = Column(String)
    _blueprint_id = Column(Integer, ForeignKey('ship_blueprint.id'))
    _blueprint = relationship('ShipBlueprint', lazy='joined')
    _flight_status = Column(Enum(FlightStatus))

    def __init__(self, owner_id, blueprint, name):
        self._owner_id = owner_id
        self._blueprint = blueprint
        self._name = name
        self._flight_status = FlightStatus.DOCKED

    def set_name(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def get_cost(self):
        return self._blueprint.get_cost()

    def get_model(self):
        return self._blueprint.get_model()

    def get_info_card(self):
        lines = []
        lines.append('Name:                     {}'.format(self._name))
        lines.append(self._blueprint.get_info_card())
        lines.append('Flight status:            {}'.format(self._flight_status.name))
        return '\n'.join(lines)

    def save(self, db):
        db.merge(self)