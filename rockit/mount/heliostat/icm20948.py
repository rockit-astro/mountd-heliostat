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
    def __init__(self, mcu, i2c_bus, accel_calibration, mag_calibration, mag_declination):
        self._mcu = mcu
        self._oid = mcu.reserve_oid()
        self._lock = threading.Lock()

        self._accel_a_inv = np.array(accel_calibration[0:9]).reshape(3, 3)
        self._accel_b = np.array(accel_calibration[9:12])
        self._mag_a_inv = np.array(mag_calibration[0:9]).reshape(3, 3)
        self._mag_b = np.array(mag_calibration[9:12])
        self._mag_declination = mag_declination

        def configure():
            self._mcu.send_command('config_i2c', oid=self._oid)
            self._mcu.send_command('i2c_set_bus', oid=self._oid, i2c_bus=i2c_bus, rate=400000, address=0x68)

        mcu.register_init_callback(configure)

        def init():
            # Reset to default settings
            self._i2c_write(0x7F, 0x00)
            self._i2c_write(0x06, 0x80)
            time.sleep(0.01)

            # Set clock, disable Gyro
            self._i2c_write(0x06, [0x01, 0x07])
            self._i2c_write(0x7F, 0x20)

            # Accelerometer sample rate to 125HZ
            self._i2c_write(0x10, [0x00, 0x08])

            # 2g full scale, enable low pass filter (mode 5)
            self._i2c_write(0x14, 0x29)

            # Configure slave i2c for magnetometer
            self._i2c_write(0x7F, 0x30)
            self._i2c_write(0x01, [0x4D, 0x01])

            # Reset the magnetometer
            self._i2c_slave_write(0x32, 0x01)
            while self._i2c_slave_read(0x32)[0] == 0x01:
                time.sleep(0.0001)

        mcu.register_post_init_callback(init)

    def _i2c_write(self, register, data):
        if not isinstance(data, list):
            data = [data]
        self._mcu.send_command('i2c_write', oid=self._oid, data=bytearray([register] + data))

    def _i2c_read(self, register, length=1):
        return self._mcu.send_query('i2c_read', oid=self._oid, reg=[register], read_len=length)

    def _i2c_slave_write(self, reg, value):
        # Copy data to ICM20948 memory
        self._i2c_write(0x7F, 0x30)
        self._i2c_write(0x03, [0x0C, reg, 0x81, value])
        self._i2c_write(0x7F, 0x00)

        # Transmit to slave AK09916
        self._i2c_write(0x03, 0x20)
        time.sleep(0.005)
        self._i2c_write(0x03, 0x00)

    def _i2c_slave_read(self, reg, length=1):
        # Copy data to ICM20948 memory
        self._i2c_write(0x7F, 0x30)
        self._i2c_write(0x03, [0x8C, reg, 0x80 | 0x08 * (length > 1) | length, 0xFF])
        self._i2c_write(0x7F, 0x00)

        # Transmit to slave AK09916
        self._i2c_write(0x03, 0x20)
        time.sleep(0.005)
        self._i2c_write(0x03, 0x00)

        # Read response from ICM20948
        return self._i2c_read(0x3B, length)

    def measure_altaz(self, samples=25, timeout=5.0):
        data = self.measure_raw(samples, timeout)

        # Calibrate into standard vectors
        accel = self._accel_a_inv @ (data[0:3] - self._accel_b)
        accel /= np.linalg.norm(accel)

        mag = self._mag_a_inv @ (data[3:6] - self._mag_b)
        mag /= np.linalg.norm(mag)
        mag[1] *= -1
        mag[2] *= -1

        # Calculate altaz from accel, mag vectors
        west = np.cross(accel, mag)
        north = np.cross(west, accel)
        azimuth = self._mag_declination - np.degrees(np.arctan2(west[0] / np.linalg.norm(west), north[0] / np.linalg.norm(north)))
        altitude = np.degrees(np.arctan2(accel[2], np.sqrt(accel[0]**2 + accel[1]**2)))
        return altitude, azimuth

    def measure_raw(self, samples=25, timeout=5.0):
        t_start = time.time()
        data = np.zeros((6, samples))
        for i in range(samples):
            # Trigger magnetometer sample
            self._i2c_slave_write(0x31, 0x01)

            # Read accelerometer
            self._i2c_write(0x7F, 0x00)
            data[0:3, i] = np.frombuffer(self._i2c_read(0x2D, 6), dtype=np.dtype('>i2')) / 2048.0

            # Read magnetometer
            while not self._i2c_slave_read(0x10)[0] & 0x01:
                if time.time() - t_start > timeout:
                    return None
                time.sleep(0.00001)

            data[3:6, i] = np.frombuffer(self._i2c_slave_read(0x11, 6), dtype=np.dtype('<i2')) * 0.15

        if samples == 1:
            return np.concatenate([data.ravel(), np.zeros(6)])

        data_clipped = SigmaClip()(data, axis=1)
        mean = np.nanmean(data_clipped, axis=1)
        std = np.nanstd(data_clipped, axis=1)
        return np.concatenate([mean, std])
