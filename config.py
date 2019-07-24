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

_config_file = 'config.json'

def get():
    return json_util.read_object_from_file(_config_file)

def write(config):
    json_util.write_object_to_file(_config_file, config)

class Config(object):
    """GrindBot config data model"""
    def __init__(self, token, db_file, db_commit_wait, admins, channel_ids):
        object.__init__(self)
        self.token = token
        self.db_file = db_file
        self.db_commit_wait = db_commit_wait
        self.admins = admins
        self.channel_ids = channel_ids
