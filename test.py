from astropy.coordinates import golden_spiral_grid
from astropy.table import Table
import astropy.units as u
import numpy as np
from rockit.common import daemons
import time
from rockit.mount.heliostat import CommandStatus

if True:
    with daemons.localhost_test.connect(timeout=60) as daemon:
        pos = daemon.read_raw_position()
        print(pos)

if False:
    coords = golden_spiral_grid(128)
    coords = coords[np.argsort(-coords.lon)]

    colnames = ['ha', 'dec']
    for prefix in ['accel', 'mag']:
        for axis in ['x', 'y', 'z']:
            for suffix in ['mean', 'med', 'std']:
                colnames.append(f'{prefix}_{axis}_{suffix}')
    has = coords.lon.wrap_at(180*u.deg).to_value(u.deg)
    decs = coords.lat.to_value(u.deg)
    decs[has > 90] = decs[has > 90] + 180
    has[has > 90] = has[has > 90] - 180
    decs[has < -90] = decs[has < -90] + 180
    has[has < -90] = has[has < -90] + 180
    decs[decs > 180] = decs[decs > 180] - 360

    has += 180

    filt = np.argsort(has)
    has = has[filt]
    decs = decs[filt]
    data = Table(names=colnames)
    for i in range(len(has)):
        ha = has[i]
        dec = decs[i]
        print(f'Slewing to {ha:.5f}, {dec:.5f} ({i+1} / {len(coords)})')
        with daemons.localhost_test.connect(timeout=180) as daemon:
            daemon.slew_hadec(ha, dec)
            time.sleep(2.5)
            pos = daemon.read_raw_position()
            data.add_row({k:v for k, v in pos.items() if k in colnames})
            data.write('raw_positions.csv', overwrite=True)
