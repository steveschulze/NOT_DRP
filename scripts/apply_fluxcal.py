#!/usr/bin/env python
import glob
import subprocess
import click
import astropy.io.fits as fits
import os
import numpy as np


def load_sens_lib():
    files = glob.glob('sens/*.fits')

    # extract mjd
    entries = {}
    for f in files:
        # TODO: ignore files that break this instead of crashing here
        mjd = int(float(os.path.basename(f).replace('.fits', ''))*10000)
        entries[mjd] = f
    return entries

@click.command()
@click.argument('frames', nargs=-1)
def main(frames):
    # load known sensfuncs {mjd -> fname}
    sensfuncs = load_sens_lib()
    sensfuncs_mjds = np.array(list(sensfuncs.keys()))
    
    entries = []
    for fname in frames:
        hdr = fits.getheader(fname)
        mjd = int(hdr['MJD']*10000)
        best_mjd = sensfuncs_mjds[np.argmin(np.abs(mjd - sensfuncs_mjds))]
        sensfile = sensfuncs[best_mjd]
        entries.append((fname, sensfile))
    ctr = 0
    while True:
        fname = 'fluxcal.%d.para' % ctr
        if os.path.isfile(fname):
            ctr += 1
            continue
        with open(fname, 'w') as f:
            f.write('[fluxcalib]\n')
            f.write('extinct_correct=True\n')
            f.write('extrap_sens=False\n')
            f.write('flux read\n')
            f.write('\tfilename | sensfile\n')
            for entry in entries:
                f.write('\t%s | %s\n' % entry)
            f.write('flux end\n')
        print('\n\ngenerated %s' % fname)
        print('Run this command to fluxcal:')
        print('\t(pipenv run) pypeit_flux_calib %s' % fname)
        print('\n\n\n')
        os.system('pypeit_flux_calib %s' % fname)

        break



if __name__ == '__main__':
    main()
