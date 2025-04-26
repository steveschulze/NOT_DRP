#!/usr/bin/env python
import subprocess
import click
import numpy as np
import os
import astropy.table as table


@click.command()
@click.option('-o', '--output', required = True)
@click.option(      '--objid', default=None)
@click.option('--overwrite', is_flag=True, help="Overwrite configuration file")
@click.argument('spectra', nargs=-1)

def main(spectra, output, objid, overwrite):
    if len(spectra) < 2:
        raise ValueError('Need at least two input spectra!')

    if os.path.isfile(output):
        if overwrite == False:
            raise ValueError('Destination file already exists!')
        else:
            print('Destination file already exists, but will be overwritten.')
    
    # find the objid for each input spectrum
    objids = []

    for fname in spectra:

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
        

        elif len(cat) == 1:
            _objid = 0

        try:
            objids.append(cat['name'][int(_objid)])

        except ValueError:
            if _objid not in cat['name']:
                raise ValueError('objid %s not found in catalog %s' % (_objid, fname_txt))
            objids.append(_objid)
        

    with open('combine.par', 'w') as f:
        f.write('[coadd1d]\n')
        f.write('coaddfile=%s\n' % output)
        f.write('\n')
        f.write('coadd1d read\n')
        f.write('filename | obj_id\n')
        for spec, objid in zip(spectra, objids):
            f.write('  %s | %s\n' % (spec, objid))
        f.write('coadd1d end\n')
    
    subprocess.run(['pypeit_coadd_1dspec', 'combine.par'])

if __name__ == '__main__':
    main()
