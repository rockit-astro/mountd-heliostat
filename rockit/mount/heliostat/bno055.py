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

import threading
import time
import numpy as np
from astropy.stats import SigmaClip

AXIS_BITS = {
    'x': (0b00, 0b0),
    'y': (0b01, 0b0),
    'z': (0b10, 0b0),
    'X': (0b00, 0b1),
    'Y': (0b01, 0b1),
    'Z': (0b10, 0b1),
}


class BNO055:
    def __init__(self, mcu, i2c_bus, calibration):
        self._mcu = mcu
        self._oid = mcu.reserve_oid()
        self._lock = threading.Lock()
        #axis_map = 'ZXy'
        def configure():
            self._mcu.send_command('config_i2c', oid=self._oid)
            self._mcu.send_command('i2c_set_bus', oid=self._oid, i2c_bus=i2c_bus, rate=400000, address=0x28)

        mcu.register_init_callback(configure)

        def init():
            # Reset chip
            self._i2c_write(0x3F, 0x20)

            time.sleep(1)

            # Remap axes
            #axis_config = [0x00, 0x00]
            #for i in range(3):
            #    bits = AXIS_BITS[axis_map[i]]
            #    axis_config[0] |= bits[0] << (2 * i)
            #    axis_config[1] |= bits[1] << i
            #self._i2c_write(0x41, axis_config)

            if calibration is not None:
                self._i2c_write(0x55, list(bytes.fromhex(calibration)))

            # ACCONLY mode
            self._i2c_write(0x3D, 0x01)

        mcu.register_post_init_callback(init)

    def _i2c_write(self, register, data):
        if not isinstance(data, list):
            data = [data]
        self._mcu.send_command('i2c_write', oid=self._oid, data=bytearray([register] + data))

    def _i2c_read(self, register, length=1):
        return self._mcu.send_query('i2c_read', oid=self._oid, reg=[register], read_len=length)

    def measure_accel(self, samples=25):
        data = np.zeros((3, samples))
        # Read accelerometer
        for i in range(samples):
            data[:, i] = np.frombuffer(self._i2c_read(0x08, 6), dtype=np.dtype('<i2')) / 100.0

        if samples == 1:
            return np.concatenate([data.ravel(), np.zeros(3)])

        data_clipped = SigmaClip()(data, axis=1)
        mean = np.nanmean(data_clipped, axis=1)
        std = np.nanstd(data_clipped, axis=1)
        return np.concatenate([mean, std])
