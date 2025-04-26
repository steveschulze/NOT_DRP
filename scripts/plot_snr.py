#!/usr/bin/env python
import click
import astropy.io.fits as fits
from   plotsettings import *
from   standard_libraries import *

@click.command()
@click.option('--wlen-min', type=float, default=4000)
@click.option('--ivar', is_flag=True)
@click.option('--noise-column', default='OPT_FLAM_SIG')
@click.option('--flux-column', default='OPT_FLAM')
@click.option('--objid', default=1)
@click.option('--wave-column', default='OPT_WAVE')
@click.argument('fname')
def main(fname, wlen_min, flux_column, wave_column, noise_column, ivar,objid):

    hdu = fits.open(fname)
    
    if len(hdu) > 2:
        print('More than one trace in output file. Specify the trace with the keyword \'--objid\' (Default: 1).')
        print('')
        hdu.info()
        print('')

    hdu = fits.open(fname)
    d   = hdu[objid].data
    
    wave = d[wave_column]
    flux = d[flux_column]
    if ivar:
        noise = 1/d[noise_column]
    else:
        noise = d[noise_column]
    
    idx = wave > wlen_min
    
    plt.figure(figsize=(9*np.sqrt(2), 9))
    ax = plt.subplot(111)
    ax.plot(wave[idx], flux[idx]/noise[idx], color='tab:blue', lw=2)

    ax.set_xlabel('Wavelength $\\left({\\rm vacuum,\\,\\AA}\\right)$')
    ax.set_ylabel('Signal-to-noise ratio')

    #plt.plot(wave[idx], flux[idx]/noise[idx])
    plt.show()



if __name__ == '__main__':
    main()
