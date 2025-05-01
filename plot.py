import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import golden_spiral_grid, spherical_to_cartesian, cartesian_to_spherical, AltAz, EarthLocation, SkyCoord
import astropy.units as u
from astropy.time import Time
import erfa
from astropy.table import Table, vstack
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from scipy import linalg

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

    E_w, E_v = linalg.eig(E)

    v_1 = E_v[:, np.argmax(E_w)]
    if v_1[0] < 0:
        v_1 = -v_1

    # v_2 (eq. 13, solution)
    v_2 = np.dot(np.dot(-linalg.inv(S_22), S_21), v_1)

    # quadratic-form parameters, parameters h and f swapped as per correction by Roger R on Teslabs page
    M = np.array([[v_1[0], v_1[5], v_1[4]],
                  [v_1[5], v_1[1], v_1[3]],
                  [v_1[4], v_1[3], v_1[2]]])
    n = np.array([[v_2[0]],
                  [v_2[1]],
                  [v_2[2]]])
    d = v_2[3]

    return M, n, d

def model_g_vector(deltas, ha, dec):
    vec = Rotation.from_euler('yxy', np.array([np.zeros_like(ha), -ha, -dec]).T + deltas.T, degrees=True).apply([0, 0, 1])
    return Rotation.from_euler('z', 180, degrees=True).apply(vec)

data = Table.read('hadec_accel.csv')
x, y, z = spherical_to_cartesian(9, data['dec'] * u.deg, data['ha'] * u.deg)
res = np.array([52.66115897, -1.58113539,  2.41943422])
ma = model_g_vector(res, np.array(data['ha']), np.array(data['dec']))

a = np.array([data['x'], data['y'], data['z']])
M, n, d = ellipsoid_fit(a)
M_inv = linalg.inv(M)
A_inv = np.real(linalg.sqrtm(M) / np.sqrt(np.dot(n.T, np.dot(M_inv, n)) - d))
b = -np.dot(M_inv, n).ravel()

# Apply correction to raw data for use in the next step
for i in range(len(data)):
    a[:, i] = A_inv @ (a.T[i] - b)

a = a.T

fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.plot(a[:, 0], a[:, 1], a[:, 2], 'b.')
ax.plot(ma[:, 0], ma[:, 1], ma[:, 2], 'r.')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
plt.show()
#ax = fig.add_subplot()
#ax.plot(x, y, 'b.')
#ax.plot(x, z, 'g.')
#ax.plot(y, z, 'r.')
#ax.set_aspect(1)
