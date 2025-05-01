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

# Sensor config based on https://github.com/pimoroni/icm20948-python (MIT licensed)
class ICM20948:
    def __init__(self, mcu, i2c_bus, calibration):
        self._mcu = mcu
        self._oid = mcu.reserve_oid()
        self._lock = threading.Lock()

        if calibration is not None:
            self._a_inv = np.array(calibration[0:9]).reshape(3, 3)
            self._b = np.array(calibration[9:12])
        else:
            self._a_inv = np.eye(3)
            self._b = np.zeros(3)

        def configure():
            self._mcu.send_command('config_i2c', oid=self._oid)
            self._mcu.send_command('i2c_set_bus', oid=self._oid, i2c_bus=i2c_bus, rate=400000, address=0x68)

        mcu.register_init_callback(configure)

        def init():
            # Reset to default settings
            self._i2c_write(0x7F, 0x00)
            self._i2c_write(0x06, 0x80)
            time.sleep(0.01)

            self._i2c_write(0x03, 0x00)

            # Set clock, disable Gyro and mag
            self._i2c_write(0x06, [0x09, 0x03])
            self._i2c_write(0x7F, 0x20)

            # Accelerometer sample rate to 125HZ
            self._i2c_write(0x10, [0x00, 0x08])

            # 2g full scale, enable low pass filter (mode 5)
            self._i2c_write(0x14, 0x29)

        mcu.register_post_init_callback(init)

    def _i2c_write(self, register, data):
        if not isinstance(data, list):
            data = [data]
        self._mcu.send_command('i2c_write', oid=self._oid, data=bytearray([register] + data))

    def _i2c_read(self, register, length=1):
        return self._mcu.send_query('i2c_read', oid=self._oid, reg=[register], read_len=length)

    def measure_accel(self, samples=25):
        data = np.zeros((3, samples))
        self._i2c_write(0x7F, 0x00)

        # Read accelerometer
        for i in range(samples):
            data[0:3, i] = np.frombuffer(self._i2c_read(0x2D, 6), dtype=np.dtype('>i2')) / 2048.0

        if samples == 1:
            return np.concatenate([data.ravel(), np.zeros(3)])

        data_clipped = SigmaClip()(data, axis=1)
        mean = np.nanmean(data_clipped, axis=1)
        std = np.nanstd(data_clipped, axis=1)
        return np.concatenate([mean, std])
