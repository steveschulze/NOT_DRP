#!/usr/bin/env python
import click
import os

@click.command()
@click.argument('date')
@click.option('--cleanup', is_flag=True, help="Remove unncessary folders and original data archive")
def main(date, cleanup):

    # Unzip archive
    os.system('unzip -o raw/{date} -d raw/'.format(date=date))

    # Flatten directory structure
    os.system('mv raw/{date}/alfosc/A*fits raw/{date}'.format(date=date))
    os.system('mv raw/{date}/alfosc/calib/A*fits raw/{date}'.format(date=date))

    # Remove old folder and zip file
    if cleanup:
        os.system('rm -rf raw/{date}/alfosc')
        os.system('rm -rf raw/{date}.zip')
    
    # Create inventory

    cmd = 'dfits -x 0 raw/{date}/*.fits | fitsort OBJECT DATE-OBS OBS_MODE IMAGETYP FAFLTNM FBFLTNM EXPTIME ALFLTNM STFLTNM AIRMASS PROPID ALAPRTNM ALGRNM NAXIS1 NAXIS2 > raw/{date}/head.info'.format(date=date)
    
    try:
        os.system(cmd)

        # and open with Visual Studio
        cmd = 'code raw/{date}/head.info'.format(date=date)
        os.system(cmd)

    except:
        print('Please check. If seems that you have not installed either dfits, fitsort or Visual studio Code.')

if __name__ == '__main__':
    main()
