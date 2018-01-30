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

import json
import jsonpickle

def read_object_from_file(json_file):
    """Uses jsonpickle to decode the contents of a file into an object."""
    try:
        with open(json_file, 'r') as f:
            content = f.read()
            return jsonpickle.decode(content)
    except FileNotFoundError:
        print('File not found: %s' % json_file)
    except json.JSONDecodeError:
        print('Error decoding json file: %s' % json_file)
    return None

def read_collection_from_file(json_file, obj_hook = None):
    """Reads the contents of a JSON file into a dict"""
    try:
        with open(json_file, 'r') as f:
            return json.load(f, object_hook = obj_hook)
    except FileNotFoundError:
        print('File not found: %s' % json_file)
    return None

def write_object_to_file(filename, data):
    """Writes an object to JSON using jsonpickle"""
    with open(filename, 'w') as f:
        f.write(json.dumps(json.loads(jsonpickle.encode(data)), indent = 4))
