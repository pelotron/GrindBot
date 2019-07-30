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
from sqlalchemy import Column, Integer, String, ForeignKey

class Cargo(DbModel):
    """
    Class that models ship cargo items
    """
    __tablename__ = 'cargo'

    id = Column(Integer, primary_key = True)
    _cargo_type = Column(String)
    _mass = Column(Integer)
    _cargo_hold_id = Column(Integer, ForeignKey('ship.id'))

    __mapper_args__ = {
        'polymorphic_identity':'cargo',
        'polymorphic_on':_cargo_type
    }

    def get_mass(self):
        return self._mass