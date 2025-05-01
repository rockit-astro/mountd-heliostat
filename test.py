from astropy.coordinates import golden_spiral_grid
from astropy.table import Table
import astropy.units as u
import numpy as np
from rockit.common import daemons
import time
import json
from rockit.mount.heliostat import CommandStatus

if False:
    with daemons.localhost_test.connect() as daemon:
        print(daemon.report_status())

if True:
    coords = golden_spiral_grid(32)
    colnames = ['ha', 'dec', 'x', 'y', 'z']

    has = coords.lon.wrap_at(180*u.deg).to_value(u.deg)
    decs = coords.lat.to_value(u.deg)

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
            time.sleep(5)
            status = daemon.report_status()

            data.add_row({
                'ha': status['ha']['pos'],
                'dec': status['dec']['pos'],
                'x': status['accel'][0],
                'y': status['accel'][1],
                'z': status['accel'][2],
            })
            data.write('hadec_accel.csv', overwrite=True)
