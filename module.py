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

from enum import Enum

class ModuleType(Enum):
    WEAPON = 0
    AUX = 1

class Module:
    """
    Cargo that can be installed in ships
    """
    
    def __init__(self, module_type):
        self._module_type = module_type

    def get_type(self):
        return self._module_type