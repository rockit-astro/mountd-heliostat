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

"""Constants and status codes used by klipper_focusd"""


class CommandStatus:
    """Numeric return codes"""
    # General error codes
    Succeeded = 0
    Failed = 1
    Blocked = 2
    InvalidControlIP = 3

    StepperNotIdle = 4
    StepperNotHomed = 5
    PositionOutsideLimits = 6
    NotConnected = 7
    NotDisconnected = 8
    NoLights = 9
    InvalidLightColor = 10
    UnknownParkPosition = 15

    _messages = {
        # General error codes
        1: 'error: command failed',
        2: 'error: another command is already running',
        3: 'error: command not accepted from this IP',
        4: 'error: stepper is not idle',
        5: 'error: stepper has not been homed',
        6: 'error: requested position outside stepper range',
        7: 'error: controller is not connected',
        8: 'error: controller is already connected',
        9: 'error: lights are not available',
        10: 'error: invalid light color',
        15: 'error: unknown park position',

        -100: 'error: terminated by user',
        -101: 'error: unable to communicate with heliostat daemon',
    }

    @classmethod
    def message(cls, error_code):
        """Returns a human readable string describing an error code"""
        if error_code in cls._messages:
            return cls._messages[error_code]
        return f'error: Unknown error code {error_code}'

class MountStatus:
    Disconnected, Connected, Homing = range(3)

    _labels = {
        0: 'OFFLINE',
        1: 'ONLINE',
        2: 'HOMING',
    }

    _colors = {
        0: 'red',
        1: 'green',
        2: 'yellow'
    }

    @classmethod
    def label(cls, status, formatting=False):
        """Returns a human readable string describing a status
           Set formatting=true to enable terminal formatting characters
        """
        if formatting:
            if status in cls._labels and status in cls._colors:
                return f'[b][{cls._colors[status]}]{cls._labels[status]}[/{cls._colors[status]}][/b]'
            return '[b][red]UNKNOWN[/red][/b]'

        if status in cls._labels:
            return cls._labels[status]
        return 'UNKNOWN'
