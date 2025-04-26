#!/usr/bin/env python
import glob
import subprocess
import click
import astropy.io.fits as fits
import os


@click.command()
@click.argument('path')
@click.option('--overwrite', is_flag=True, help="Overwrite configuration file")

def main(path, overwrite):
    print(' * Searching for std frames in %s' % path)
    std_1dframes = glob.glob('%s/spec1d*.fits' % path)

    
    for frame in std_1dframes:
        hdr = fits.getheader(frame)
        mjd = hdr['MJD']
        dest_path = 'sens/%.4f.fits' % mjd
        print(' * %s -> %s' % (frame, dest_path))

        if os.path.isfile(dest_path):
            if overwrite == False:
                raise ValueError('* ERR: already exists!')
            else:
                print('Destination file already exists, but will be overwritten.')

        subprocess.run(['pypeit_sensfunc', '-s', 'etc/sensfunc.par', frame, '-o', dest_path, '--debug'])

if __name__ == '__main__':
    main()
