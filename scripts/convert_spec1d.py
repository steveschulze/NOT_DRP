#!/usr/bin/env python

from   astropy import time
import click
from   misc import bcolors
from   plotsettings import *
from   standard_libraries import *

def create_header(param_file, obs_name, red_name):

    # Convert the Pypeit parameter file into a table and only keep the science files.

    data_pypeit       = open(param_file, mode='r')
    table_pypeit      = []

    for line in data_pypeit.readlines():
        if line[0] == '|':
            table_pypeit.append(line.replace(' ', '').split('|')[1:-1])
        
        elif 'scidir' in line:
            scidir = line.split('=')[-1].split(' ')[-1][:-1]

    table_pypeit            = table.Table(np.array(table_pypeit)[1:], names=np.array(table_pypeit)[0])
    table_pypeit            = table_pypeit[table_pypeit['frametype'] == 'science']
    table_pypeit['mjd']     = [float(x) for x in table_pypeit['mjd']]
    table_pypeit['exptime'] = [float(x) for x in table_pypeit['exptime']]
    table_pypeit['flag']    = False
    table_pypeit.sort('filename')

    # Sanity check: Reduction includes only data of 1 object and 1 setup

    if len(np.unique(table_pypeit['target'])) != 1 | len(np.unique(table_pypeit['decker'])) != 1 | len(np.unique(table_pypeit['dispname'])) != 1:
        print(table_pypeit)
        print(bcolors.FAIL + 'ERROR: Dataset contains observations of multiple objects or observing modes.' + bcolors.ENDC)
        sys.exit()

    # Get a list of all science file that were created

    sci_files = glob.glob(scidir+'/spec1d*fits')
    sci_files = sorted(sci_files)
    
    # Match Pypeit paramter file with the list of final science files.
    
    for ii, file in enumerate(table_pypeit['filename']):
        if np.any([True if file.split('.')[0] in x else False for x in sci_files]):
            table_pypeit['flag'][ii] = True

    table_pypeit = table_pypeit[table_pypeit['flag']]

    # Prepare header

    # Original header
    header_orig = fits.open(glob.glob('raw/*/{}'.format(table_pypeit['filename'][0]))[0])[0].header
    
    # Header after the data reduction
    hdulist_pypeit            = fits.open(sci_files[0])
    header_pypeit             = hdulist_pypeit[0].header
    header_pypeit_2           = hdulist_pypeit[1].header
    reduction_history         = header_pypeit['HISTORY']

    # Build the header

    comments                  = {}
    comments['HEADER']        = 'START'
    comments['OBJECT']        = table_pypeit['target'][0]

    # Object properties

    comments['RA']            = header_orig['OBJRA']
    comments['DEC']           = header_orig['OBJDEC']
    comments['EQUINOX']       = header_orig['OBJEQUIN']
    comments['RADECSYS']      = header_orig['RADECSYS']
    comments['OBJPMRA']       = header_orig['OBJPMRA']
    comments['OBJPMDEC']      = header_orig['OBJPMDEC']

    # Facility details

    comments['OBSERVATORY']   = header_orig['OBSERVAT']
    comments['TELESCOPE']     = 'NOT'
    comments['LON-OBS']       = header_pypeit['LON-OBS']
    comments['LAT-OBS']       = header_pypeit['LAT-OBS']
    comments['ALT-OBS']       = header_pypeit['ALT-OBS']
    comments['INSTRUMENT']    = 'ALFOSC'
    comments['DETECTOR']      = header_orig['DETNAME']
    comments['CHIPID']        = header_orig['CHIPID']

    # Observation details

    comments['DATE-OBS']      = time.Time(min(table_pypeit['mjd']), format='mjd').isot
    comments['JD']            = np.round(time.Time(min(table_pypeit['mjd']), format='mjd').jd, 5)
    comments['MJD']           = np.round(min(table_pypeit['mjd']), 5)
    comments['EXPTIME']       = np.sum(table_pypeit['exptime'])
    comments['NCOMBINE']      = len(table_pypeit)
    comments['INTTIME']       = table_pypeit['exptime'][0]
    comments['SLIT']          = np.unique(table_pypeit['decker'])[0]
    comments['DISERPER']      = np.unique(table_pypeit['dispname'])[0]
    comments['BINNING']       = header_pypeit['BINNING']
    comments['AIRMASS_START'] = header_pypeit['AIRMASS']
    comments['DETWIN1']       = header_orig['DETWIN1']

    # Observing program
    comments['PROPID']        = header_orig['PROPID']
    comments['PROPTITL']      = header_orig['PROPTITL']
    comments['NOT_OBSERVER']  = header_orig['OBSERVER']
    comments['HOME_OBSERVER'] = 'Jesper Sollerman, {}'.format(obs_name)
    comments['REDUCER']       = red_name
    comments['GROUPID']       = header_orig['GROUPID']
    comments['BLOCKID']       = header_orig['BLOCKID']

    # Pipeline details
    comments['PIPELINE']      = 'PypeIt v{}'.format(header_pypeit['VERSPYP'])
    comments['WLENSYSTEM']    = 'vacuum'
    comments['FLUX_FACTOR']   = '1e-17'
    comments['EXTENSION']     = header_pypeit['EXT0000']
    comments['WAVE_RMS_PX']   = header_pypeit_2['WAVE_RMS']
    comments['PSF_FWHM_PX']   = header_pypeit_2['FWHM']

    for ii in range(len(reduction_history)):
        comments['HISTORY {}'.format(ii)] = reduction_history[ii]

    comments['HEADER']        = 'END'
    return comments
    

@click.command()
@click.argument('fname', nargs=1, required=True)
@click.argument('param_file', nargs=1, required=True)
@click.option('--objid', default=None)
@click.option('--obs-name', default='Steve Schulze')
@click.option('--red-name', default='Steve Schulze')
@click.option('--wlen-min', type=float, default=4000)

def main(fname, param_file, wlen_min, obs_name, red_name, objid):

    try:
        # If an object has only 1 exposure (i.e., you didn't use combine_spectra.py)

        _objid = objid

        fname_txt = fname.replace('.fits', '.txt')
        cat = table.Table.read(fname_txt, format='ascii.fixed_width')

        cat['objid'] = np.linspace(0, len(cat)-1, len(cat), dtype=int)
        print(cat[['objid', 'slit', 'name', 'spat_pixpos', 'spat_fracpos', 'box_width', 'opt_fwhm', 's2n']])

        if len(cat) > 1 and objid is None:
            # If there is more than 1 
            # We select the center pixel (closest to 250)
            pixpos = cat['spat_pixpos']
            idx_pixpos_middle = np.argmin([np.abs(p-250) for p in pixpos])
            _objid = idx_pixpos_middle

            msg = 'Pypeit extracted multiple spectra. We assume that you want to have the trace closest to y=250 px.capitalize().\n Use the keyword \'--objid\' if this is not your preferred choice.'
            print(msg)

        else:
            _objid = objid

        data              = table.Table.read(fname, hdu=cat['name'][int(_objid)]) 

    except:
        # If an object has more than 1 exposure (i.e., you used combine_spectra.py)
        data              = table.Table.read(fname, hdu=1) 

    # Header
    header            = create_header(param_file, obs_name, red_name)

    # Create output files

    waves = [3000, 3250, 3500, 3850, wlen_min]

    for x in waves:

        # Read data


        # Select right column labels for wavelength, flux and error 
        # PypeIt changes column names if 1D spectra were co-added

        wave_column = 'OPT_WAVE'      if 'OPT_WAVE'      in data.keys() else 'wave'
        flux_column = 'OPT_FLAM'      if 'OPT_FLAM'      in data.keys() else 'flux'
        err_column  = 'OPT_FLAM_IVAR' if 'OPT_FLAM_IVAR' in data.keys() else 'ivar'

        try:
            data.sort('OPT_WAVE')
        except:
            data.sort('wave')

        # Post-process

        # Get the data with lambda >= lambda_cut
        mask_good   = data[wave_column] >= x

        # Convert inverse variance to 1-sigma error
        data['err'] = pow(data[err_column], -0.5)
        
        t = table.Table([data[wave_column][mask_good], data[flux_column][mask_good], data[err_column][mask_good]], names=('wave', 'flux', 'err'))
        t.meta['comments']  = list([key + ': ' +  str(header[key]) for key in list(header.keys())]) + ['COLUMNS: WAVE FLUX FLUX_ERR']

        new_fname = os.path.basename(fname).replace('.fits', '_' + str(int(x)) + '.ascii')
        t.write(new_fname, format='ascii.no_header', overwrite=True)

    # Diagnostic plot

    plt.figure(figsize=(9*np.sqrt(2), 9))
    ax = plt.subplot(111)

    ax.errorbar(data[wave_column], data[flux_column], color='tab:blue', lw=1)

    idx = data[wave_column] > 4000

    ax.set_xlim(2950, 10000)
    ax.set_ylim(0, max(data[flux_column][idx])*1.05)

    ax.set_xlabel('Wavelength $\\left({\\rm vacuum,\\,\\AA}\\right)$')
    ax.set_ylabel('$F_\\lambda \\left(10^{-17}\\,{\\rm erg\\,cm}^{-2}\\,{\\rm s}^{-1}\\,{\\rm \\AA}^{-1}\\right)$ ')

    
    for idx, wave in enumerate(waves):
        ax.axvline(wave, lw=2 + idx, color='k', zorder=999)

    plt.savefig(new_fname.replace('ascii', 'pdf').replace('_' + str(int(wlen_min)), ''))
    plt.show()
    plt.close()


if __name__ == '__main__':
    main()
