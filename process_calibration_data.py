import argparse as ap
import numpy as np
from scipy import linalg
from astropy.table import Table
from astropy.coordinates import cartesian_to_spherical, spherical_to_cartesian
import json
from erfa import ae2hd, seps
import matplotlib.pyplot as plt

# Based on https://github.com/jremington/ICM_20948-AHRS
def ellipsoid_fit(s):
    """ Estimate ellipsoid parameters from a set of points.

        Parameters
        ----------
        s : array_like
          The samples (M,N) where M=3 (x,y,z) and N=number of samples.

        Returns
        -------
        M, n, d : array_like, array_like, float
          The ellipsoid parameters M, n, d.

        References
        ----------
        .. [1] Qingde Li; Griffiths, J.G., "Least squares ellipsoid specific
           fitting," in Geometric Modeling and Processing, 2004.
           Proceedings, vol., no., pp.335-340, 2004
    """

    # D (samples)
    D = np.array([s[0] ** 2., s[1] ** 2., s[2] ** 2.,
                  2. * s[1] * s[2], 2. * s[0] * s[2], 2. * s[0] * s[1],
                  2. * s[0], 2. * s[1], 2. * s[2], np.ones_like(s[0])])

    # S, S_11, S_12, S_21, S_22 (eq. 11)
    S = np.dot(D, D.T)
    S_11 = S[:6, :6]
    S_12 = S[:6, 6:]
    S_21 = S[6:, :6]
    S_22 = S[6:, 6:]

    # C (Eq. 8, k=4)
    C = np.array([[-1, 1, 1, 0, 0, 0],
                  [1, -1, 1, 0, 0, 0],
                  [1, 1, -1, 0, 0, 0],
                  [0, 0, 0, -4, 0, 0],
                  [0, 0, 0, 0, -4, 0],
                  [0, 0, 0, 0, 0, -4]])

    # v_1 (eq. 15, solution)
    E = np.dot(linalg.inv(C), S_11 - np.dot(S_12, np.dot(linalg.inv(S_22), S_21)))

    E_w, E_v = np.linalg.eig(E)

    v_1 = E_v[:, np.argmax(E_w)]
    if v_1[0] < 0:
        v_1 = -v_1

    # v_2 (eq. 13, solution)
    v_2 = np.dot(np.dot(-np.linalg.inv(S_22), S_21), v_1)

    # quadratic-form parameters, parameters h and f swapped as per correction by Roger R on Teslabs page
    M = np.array([[v_1[0], v_1[5], v_1[4]],
                  [v_1[5], v_1[1], v_1[3]],
                  [v_1[4], v_1[3], v_1[2]]])
    n = np.array([[v_2[0]],
                  [v_2[1]],
                  [v_2[2]]])
    d = v_2[3]

    return M, n, d

def fit_measurements(path):
    data = Table.read(path)
    data = data[data['dec'] > -90]
    data = data[data['dec'] < 90]

    for param in ['accel', 'mag']:
        s = np.array([data[f'{param}_x_mean'], data[f'{param}_y_mean'], data[f'{param}_z_mean']])
        M, n, d = ellipsoid_fit(s)
        M_inv = linalg.inv(M)
        A_inv = np.real(linalg.sqrtm(M) / np.sqrt(np.dot(n.T, np.dot(M_inv, n)) - d))
        b = -np.dot(M_inv, n).ravel()
        print(f'"{param}_calib": [')
        for j in range(3):
            print('  ' + ', '.join(f'{x:.5e}' for x in A_inv[j, :]) + ',')
        print('  ' + ', '.join(f'{x:.5e}' for x in b))
        print('],')

        # Apply correction to raw data for use in the next step
        for i in range(len(data)):
            xyz = A_inv @ (s[:, i] - b)
            for j, ax in enumerate(['x', 'y', 'z']):
                data[f'{param}_{ax}_mean'][i] = xyz[j]

    # Align magnetometer axes to match accelerometer
    data['mag_y_mean'] = -data['mag_y_mean']
    data['mag_z_mean'] = -data['mag_z_mean']

    # Calculate compass north
    accel = np.array([data['accel_x_mean'], data['accel_y_mean'], data['accel_z_mean']])
    accel /= np.linalg.norm(accel, axis=0)

    mag = np.array([data['mag_x_mean'], data['mag_y_mean'], data['mag_z_mean']])
    mag /= np.linalg.norm(mag, axis=0)

    west = np.cross(accel, mag, axis=0)
    west /= np.linalg.norm(west)

    north = np.cross(west, accel, axis=0)
    north /= np.linalg.norm(north)

    # Calculate altaz from measurements
    el = np.arctan2(data['accel_z_mean'], np.sqrt(data['accel_x_mean']**2 + data['accel_y_mean']**2))
    az = -np.arctan2(west[0], north[0])

    import astropy.units as u
    from astropy.coordinates import SkyCoord, EarthLocation, AltAz
    from astropy.time import Time
    location = EarthLocation(
        lat=52.376861 * u.deg,
        lon=-1.583861 * u.deg,
        height=94 * u.m)
    t = Time(Time.now(), location=location)
    foo = SkyCoord(data['ha'], data['dec'], frame='hadec', unit=u.deg, obstime=t, location=location)
    foo = foo.transform_to(AltAz(obstime=t))

    # Calculate polar axis from altaz
    #ha, dec = ae2hd(az, el, np.radians(52.37))

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    x, y, z = spherical_to_cartesian(1, foo.alt, foo.az)
    x, y, z = 10*north
    ax.plot(x, y, z, 'r.', ms=25)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')

    x, y, z = spherical_to_cartesian(1, el*u.rad, az*u.rad)
    #ax.plot(x, y, z, 'b.', ms=25)

    #plt.plot(foo.az.to_value(u.deg), foo.alt.to_value(u.deg), 'r.')
    #plt.plot(np.degrees(az), np.degrees(el), 'b.')
    plt.show()



if __name__ == '__main__':
    fit_measurements('raw_positions_a.csv')
