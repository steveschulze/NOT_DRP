#!/usr/bin/env python
import click
import os

import astropy.io.fits as fits
import astropy.time as time




@click.command()
@click.argument('fits_files', nargs=-1)
def main(fits_files):
    print('|        filename | frametype |            ra |           dec |          target | dispname |   decker | binning |                mjd |         airmass |  exptime |')
    for fname in fits_files:
        hdr = fits.getheader(fname)
        ra, dec = hdr['RA'], hdr['DEC']
        target = hdr['OBJECT']
        grism = hdr['ALGRNM'].replace('#', '')
        slit = hdr['ALAPRTNM']
        binning = '1,1'
        mjd = time.Time(hdr['DATE-OBS']).mjd
        airmass = hdr['AIRMASS']
        exptime = hdr['EXPTIME']

        frametype = None
        if hdr['IMAGETYP'] == 'BIAS':
            frametype = 'bias'
        elif hdr['IMAGETYP'] == 'OBJECT':
            frametype = 'science'
        elif hdr['IMAGETYP'] == 'WAVE,LAMP':
            frametype = 'tilt,arc'
        elif hdr['IMAGETYP'] == 'FLAT,LAMP':
            frametype = 'trace,illumflat,pixelflat'

        basename = os.path.basename(fname)

        print(f"| {basename} | {frametype} | {ra} | {dec} | {target} | {grism} | {slit} | {binning} | {mjd} | {airmass} | {exptime} |")




if __name__ == '__main__':
    main()
