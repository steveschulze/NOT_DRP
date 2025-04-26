#!/usr/bin/env python
import click
from   plotsettings import *
from   standard_libraries import *

@click.command()
@click.option('--wlen-min', type=float, default=3000)
@click.argument('filename')
def main(filename, wlen_min):

    hdu = table.Table.read(filename, hdu=1)

    wave = hdu['SENS_WAVE'].data
    sensfunc = hdu['SENS_ZEROPOINT'].data

    idx = wave > wlen_min

    plt.figure(figsize=(9*np.sqrt(2), 9))
    ax = plt.subplot(111)
    ax.plot(wave[idx], sensfunc[idx], color='tab:blue', lw=2)

    ax.set_xlabel('Wavelength $\\left({\\rm vacuum,\\,\\AA}\\right)$')
    ax.set_ylabel('Sensivity function')

    plt.show()

if __name__ == '__main__':
    main()
