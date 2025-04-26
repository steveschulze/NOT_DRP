#!/usr/bin/env python
import click
import astropy.io.fits as fits
import glob
import ccdproc
import astropy.coordinates as coordinates
import astropy.units as u
import astropy.time as time
import numpy as np
import jinja2
import os

LRIS_HEADERS = [
    'DATE-OBS',
    'UTC',
    'RA',
    'DEC',
    'OBJECT',
    'GRISNAME',
    'GRANAME',
    'SLITNAME',
    'BINNING',
    'AIRMASS',
    'ELAPTIME',
    'DICHNAME',
    'NUMAMPS',
    'TRAPDOOR',
    'WAVELEN',
    'TRAPDOOR',
    'MERCURY',
    'NEON',
    'ARGON',
    'CADMIUM',
    'ZINC',
    'HALOGEN',
    'KRYPTON',
    'XENON',
    'FEARGON',
    'DEUTERI'
]

PYPEIT_TEMPLATE = jinja2.Template("""
# User-defined execution parameters
[rdx]
spectrograph = not_alfosc
scidir = {{ sci_dir }}
qadir = {{ qa_dir }}

[calibrations]
calib_dir = {{ calibs_dir }}

[reduce]
  [[findobj]]
    snr_thresh = 5

# Setup
setup read
 Setup B:
   --:
     dispname: {{ disperser }}
     dichroic: {{ dichroic }}
       decker: {{ slit }}
          amp: {{ amp }}
      binning: {{ binning }}
    dispangle: {{ dispangle }}
      cenwave: {{ cenwave }}
setup end

# Read in the data
data read
 path {{ raw_data_dir }}
|           filename |                 frametype |                 ra |                 dec |        target | dispname |   decker | binning |          mjd | airmass |        exptime | dichroic | amp | dispangle |     cenwave |  hatch |                  lampstat01 |    dateobs |
{% for x in raw_files -%}
| {{ x.filename }}| {{ x.frametype }} | {{ x.ra }} | {{ x.dec }} | {{ x.target }} | {{ x.disperser }} | {{ x.slit }} | {{ x.binning }} | {{ x.mjd }} | {{ x.airmass }} | {{ x.exptime }} | {{ x.dichroic}} | {{ x.amp }} | {{ x.dispangle }} | {{ x.cenwave}} | {{ x.hatch }} | {{ x.lampstat01 }} | {{ x.dateobs }} |
{% endfor %}
data end
""")

def lamp_keyword(header):

    # Reference: https://github.com/pypeit/PypeIt/blob/release/pypeit/spectrographs/keck_lris.py

    # lamp status header keywords
    lamp_keys = ['MERCURY', 'NEON', 'ARGON', 'CADMIUM', 'ZINC', 'HALOGEN',
                         'KRYPTON', 'XENON', 'FEARGON', 'DEUTERI']
    
    # pypeit lamp names
    lamp_names = np.array(['HgI', 'NeI', 'ArI', 'CdI', 'ZnI', 'Halogen', 'KrI', 'XeI', 'FeAr', '2H'])

    old_lamp_status = np.array(header.get('LAMPS').split(','), dtype=int).astype(bool) \
                if header.get('LAMPS') is not None else None
    
    new_lamp_status = np.array([header.get(k) == 'on' for k in lamp_keys])
    
    where_on = np.where(new_lamp_status)[0] if old_lamp_status is None else np.where(old_lamp_status)[0]
    
    if where_on.size > 0:
        return ' '.join(lamp_names[where_on])


def extract_frame(hdrs, idx, frametype):
    h = hdrs.summary[idx]
    ret = {
        'filename': os.path.basename(h['file']),
        'frametype': frametype,
        'ra': h['RA'],
        'dec': h['DEC'],
        'target': h['OBJECT'],
        'grism': h['GRISNAME'],
        'grating': h['GRANAME'],
        'slit': h['SLITNAME'],
        'binning': h['BINNING'][::-1],
        'mjd': time.Time(h['DATE-BEG']).mjd,
        'airmass': h['AIRMASS'],
        'exptime': h['ELAPTIME'],
        'dichroic': h['DICHNAME'],
        'amp': h['NUMAMPS'],
        'dispangle': h['TRAPDOOR'],
        'cenwave': h['WAVELEN'],
        'lampstat01': lamp_keyword(h),
        'hatch': h['TRAPDOOR'],
        'dateobs': h['DATE-OBS']
    }
    return ret


def produce_dataset(hdrs, frame_idx, raw_dir, day, target_name, overwrite):

    coords = coordinates.SkyCoord(hdrs.summary['RA'], hdrs.summary['DEC'], unit=(u.deg, u.deg))

    # FIXME: this assumes one instrument configuration per target
    assert len(np.unique(hdrs.summary['DETWIN1'][frame_idx])) == 1
    detwin1 = hdrs.summary['DETWIN1'][frame_idx][0]

    # list of frames to use in the pypeit template
    frames = []
    
    # find bias frame with same DETWIN1 configuration
    bias_frames = np.logical_and(hdrs.summary['IMAGETYP'] == 'BIAS', hdrs.summary['DETWIN1'] == detwin1)
    for idx in np.arange(len(hdrs.summary))[bias_frames]:
        frames.append(extract_frame(hdrs, idx, 'bias'))

    # FIXME: we assume that one target has one set of coordinates
    # TODO: ensure that
    sci_coords   = coordinates.SkyCoord(hdrs.summary['RA'][frame_idx][0], hdrs.summary['DEC'][frame_idx][0], unit=(u.deg, u.deg))
    frame_offset = sci_coords.separation(coords)

    # now find the matching arcs for that observation
    wave_idx = np.logical_and(hdrs.summary['IMAGETYP'] == 'WAVE,LAMP', frame_offset < 1*u.deg)
    flat_idx = np.logical_and(hdrs.summary['IMAGETYP'] == 'FLAT,LAMP', frame_offset < 1*u.deg)

    for idx in np.arange(len(hdrs.summary))[wave_idx]:
        frames.append(extract_frame(hdrs, idx, 'tilt,arc'))
    for idx in np.arange(len(hdrs.summary))[flat_idx]:
        frames.append(extract_frame(hdrs, idx, 'trace,illumflat,pixelflat'))

    for idx in np.arange(len(hdrs.summary))[frame_idx]:
        frames.append(extract_frame(hdrs, idx, 'science'))

    dest_file = 'datasets/%s-%s.pypeit' % (day, target_name)
    header_file = 'datasets/%s-%s.header' % (day, target_name)
    
    if os.path.isfile(dest_file):
        if overwrite != True:
            print('   * %s Already exists. Skipping' % dest_file)
            return

    calibs_dir = 'calibs/%s-%s' % (day, target_name)
    sci_dir = 'sci/%s-%s' % (day, target_name)
    qa_dir = 'QA/%s-%s' % (day, target_name)
    
    print('   * Generating pypeit file %s' % dest_file)
    with open(dest_file, 'w') as f:
        f.write(PYPEIT_TEMPLATE.render(raw_files=frames, grism=frames[-1]['grism'], slit=frames[-1]['slit'], raw_data_dir=raw_dir, calibs_dir=calibs_dir, sci_dir=sci_dir, qa_dir=qa_dir))

@click.command()
@click.argument('day')
@click.argument('arm')
@click.option('--overwrite', is_flag=True, help="Overwrite configuration file")
def main(day, arm, overwrite):
    print('Producing datasets for %s' % day)
    fits_dir = 'raw/{day}/{arm}'.format(day=day, arm=arm)
    fits_files = glob.glob('%s/*.fits' % fits_dir)
    print(' * Found %d frames' % len(fits_files))
    
    # load headers
    print(' * Loading headers..')
    hdrs = ccdproc.ImageFileCollection(fits_dir, keywords=LRIS_HEADERS)
    print(hdrs.summary)
    
    """

    # find the standard frames
    std_frames = np.logical_and(hdrs.summary['IMAGETYP'] == 'STD', hdrs.summary['IMAGECAT'] == 'CALIB')
    print(' * Found %d STD frames' % np.count_nonzero(std_frames))
    
    # find the science frames
    sci_frames = hdrs.summary['IMAGECAT'] == 'SCIENCE'
    print(' * Found %d SCI frames' % np.count_nonzero(sci_frames))

    std_names = np.unique(hdrs.summary['OBJECT'][std_frames])
    sci_names = np.unique(hdrs.summary['OBJECT'][sci_frames])

    for std_tgt_name in std_names:
        print(' * STD-%s' % std_tgt_name)
        idx = np.logical_and(std_frames, hdrs.summary['OBJECT'] == std_tgt_name)
        produce_dataset(hdrs, idx, fits_dir, day, 'STD-%s' % std_tgt_name, overwrite)

    for sci_tgt_name in sci_names:
        print(' * %s' % sci_tgt_name)
        idx = np.logical_and(sci_frames, hdrs.summary['OBJECT'] == sci_tgt_name)
        produce_dataset(hdrs, idx, fits_dir, day, sci_tgt_name, overwrite)
    """

if __name__ == '__main__':
    main()
