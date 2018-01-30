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
from sqlalchemy import Column, Integer, String

class Character(DbBase):
    __tablename__ = 'character'

    id = Column(Integer, primary_key = True)
    name = Column(String)
    uptime = Column(Integer)
    owner_id = Column(String)

    def __repr__(self):
        return '<Character(name = %s, uptime = %d, owner_id = %s)>' % (
            self.name, self.uptime, self.owner_id)
