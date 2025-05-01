#
# This file is part of the Robotic Observatory Control Kit (rockit)
#
# rockit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rockit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rockit.  If not, see <http://www.gnu.org/licenses/>.

"""Helper function to validate and parse the json config file"""

import json
from rockit.common import daemons, IP, validation
from rockit.klippermcu.schema import gpio_schema, interfaces_schema, neopixel_schema, stepper_schema

CONFIG_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['daemon', 'log_name', 'control_machines',
                 'serial_port', 'serial_baud',
                 'latitude', 'longitude', 'altitude',
                 'connect_timeout', 'move_timeout', 'home_timeout',
                 'ha', 'dec', 'focus'],
    'properties': {
        'daemon': {
            'type': 'string',
            'daemon_name': True
        },
        'log_name': {
            'type': 'string',
        },
        'control_machines': {
            'type': 'array',
            'items': {
                'type': 'string',
                'machine_name': True
            }
        },
        'serial_port': {
            'type': 'string',
        },
        'serial_baud': {
            'type': 'integer',
            'minimum': 250000,
            'maximum': 250000
        },
        'latitude': {
            'type': 'number',
            'minimum': -90,
            'maximum': 90
        },
        'longitude': {
            'type': 'number',
            'minimum': -180,
            'maximum': 180
        },
        'altitude': {
            'type': 'number',
            'minimum': 0
        },
        'connect_timeout': {
            'type': 'number',
            'minimum': 0
        },
        'move_timeout': {
            'type': 'number',
            'minimum': 0
        },
        'home_timeout': {
            'type': 'number',
            'minimum': 0
        },
        'controller_fan': gpio_schema(),
        'neopixel': neopixel_schema(),
        'interfaces': interfaces_schema(tmc2209=True),
        'ha': stepper_schema(require_uart=True, require_endstop=True, require_tracking=True),
        'dec': stepper_schema(require_uart=True, require_endstop=True, require_tracking=True),
        'focus': stepper_schema(require_uart=True, require_endstop=True, require_tracking=True)
    }
}

class Config:
    """Daemon configuration parsed from a json file"""
    def __init__(self, config_filename):
        # Will throw on file not found or invalid json
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config_json = json.load(config_file)

        # Will throw on schema violations
        validation.validate_config(config_json, CONFIG_SCHEMA, {
            'daemon_name': validation.daemon_name_validator,
            'machine_name': validation.machine_name_validator,
        })

        self.daemon = getattr(daemons, config_json['daemon'])
        self.log_name = config_json['log_name']
        self.control_ips = [getattr(IP, machine) for machine in config_json['control_machines']]
        self.serial_port = config_json['serial_port']
        self.serial_baud = int(config_json['serial_baud'])
        self.latitude = float(config_json['latitude'])
        self.longitude = float(config_json['longitude'])
        self.altitude = float(config_json['altitude'])
        self.connect_timeout = float(config_json['connect_timeout'])
        self.move_timeout = float(config_json['move_timeout'])
        self.home_timeout = float(config_json['home_timeout'])
        self.controller_fan = config_json.get('controller_fan', None)
        self.neopixel = config_json.get('neopixel', None)
        self.interfaces = config_json.get('interfaces', {})
        self.ha_stepper = config_json['ha']
        self.dec_stepper = config_json['dec']
        self.focus_stepper = config_json['focus']
