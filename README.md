# Collection of scripts to rapidly reduce NOT/ALFOSC spectra

Originally developed by Tassio Schweyer. Since then modified. Clone of [https://gitlab.com/steveschulze/pypeit_alfosc_env](https://gitlab.com/steveschulze/pypeit_alfosc_env).

# Installation

Install a python 3 environment for pypeit. For instance, using pipenv and python3

> pipenv install

Or using anaconda

> conda install -c conda-forge pypeit

Also install `astropy`, `ccdproc`, `click` and `jinja2`. Copy `misc.py`, `plotsettings.py` and `standard_libraries.py` to your standard python libary folder. Also install `dfits` and `fitsort`.

# Usage

All commands need to be executed with the current working directory being in the top directory of this git repository (directory where this README is located).

## Prepare observations

If you download data from the cloud storage, store the data in `raw`and do

>(pipenv run) scripts/prepare_dataset.py 2020-07-07

This unpacks the archive and create the summary file `head.info` with all relevant header information. The file will be opened with Visual Studio. If you want to remove the archive or unnecessary directories, add the option `--cleanup`.

If you retrieve data from the archive

>Download data (science + calib) to raw/2020-07-07/

Generate the PypeIt parameter files

> (pipenv run) scripts/create_datasets.py 2020-07-07

This will create the relevant datasets for science and standards in datasets. Use the option `--overwrite` if you want to overwrite the previous instance.

Notes:
* This steps is also needed for PyNOT.

## Reducing all datasets

> (pipenv run) run_pypeit datasets/2020-07-07-STD-SP2209+178.pypeit

(same for each dataset)

If you want to process multiple data sets at ones do 

>ls dataset/2020-07-07-*.pypeit | xargs -P 8 -n 1 run_pypeit

The parameter `P` controls the number of parallel sessions.

Notes:
* The wavelength calibration is in [vacuum](https://pypeit.readthedocs.io/en/release/calibrations/wave_calib.html).
* Sometimes a flat is missing resulting in crashing `PypeIt`. You can use the flat from a different object. Open the relevant parameter files and copy the line with the frame type `trace,illumflat,pixelflat`.
* Do not mix arc of different objects. There is a noticeable flexure in the optical path, resulting in a wavelength shift.
* From the PypeIt Manual: 
  >Whenever you upgrade PypeIt, beware that this may include changes to the output file data models. These changes are not required to be backwards-compatible, meaning that, e.g., pypeit_show_2dspec may fault when trying to view spec2d* files produced with your existing PypeIt version after upgrading to a new version. The best approach is to always re-reduce data you’re still working with anytime you update PypeIt.

## Creating sensitivity function

This will automatically match all standard star targets that were reduced (or try to anyway).

> (pipenv run) scripts/create_sensfunc.py 2020-07-07

This will create a new sensitivity file for the MJD and place it into sens. Use the option `--overwrite` if you want to overwrite the previous instance.

If you want to inspect the sensitivity function at a later stage do

> (pipenv run) scripts/plot_sens.py sens/59038.2281.fits

Notes:
* Inspect the flux calibration very carefully. The regions at ~4000 Å and >9000 Å can be challenging. To tweak the flux calibration, modify the options `polyorder`, `hydrogen_mask_wid` in `etc/sensfunc.par`.

## Flux calibrating spectra

This will automatically search for the correct sens file in the sens dir and apply it to the spectra.

> (pipenv run) scripts/apply_fluxcal.py sci/2020-07-07-*/spec1d*.fits

If you have multiple objects, you can speed this up via

>ls sci/2020-07-07-ZTF*/spec1d*fits | xargs -P 1 -n 1 scripts/apply_fluxcal.py

Notes:
* Do not increase the value of `P`!

## Inspecting spectra

> (pipenv run) pypeit_show_1dspec sci/*/spec1d_ALDg070110-ZTF20abfehpe_ALFOSC_2020Jul08T000441.463.fits --flux

To plot SNR over wavelength for a spec
> (pipenv run) scripts/plot_snr.py sci/*/spec1d_ALDg070088-ZTF18acqugen_ALFOSC_2020Jul07T221416.630.fits

Notes:
* If more than one object was identified, use the option `--exten ` to choose object of interest.


## Combining spectra

> (pipenv run) scripts/combine_spectra.py -o ztf20aau_combine.fits sci/2020-07-07-ZTF20aauoktk/spec1d_ALDg07009*.fits

Will combine the spec1d frames into the destination file specified with `-o`

If multiple spectra are extracted, the script will automatically select the trace closest to pixel 250. You can manually select the trace using the keyword `--objid <number>`. The ID should be taken from the table shown on your screen.

Use the option `--overwrite` if you want to overwrite the previous instance.

## Converting to ASCII

> (pipenv run) scripts/convert_spec1d.py sci/2020-07-07-ZTF20aauoktk/spec1d_ALDg07009.fits datasets/2020-07-07-ZTF20aauoktk.pypeit

Will create four text files `spec1d_ALDg07009_*.ascii` with different cut-offs in the blue. The default values are 3000, 3250, 3500, 3850 and 4000 Å. The last value can be tweaked with the keyword `--wlen-min`. The text file contain a crude header about the observation. In addition, a figure called `spec1d_ALDg07009*.pdf` is created.

The routine has two optional arguments `--obs-name` and `--red-name` to specify who performed the observations and who reduced the data. Write the name or list of names in quotation marks, e.g., `"John Doe"` or `"Jane Doe, John Doe"`.

If multiple spectra are in the final fits file, the script will automatically select the trace closest to pixel 250. You can manually select the trace using the keyword `--objid <number>`. The ID should be taken from the table shown on your screen.


## Upload to Fritz

Open `scripts/upload_fritz_pypeit.ipynb` and follow the instructions. To run this script you need to have an upload token. The file `scripts/upload_fritz_pynot.ipynb` is for spectra reduced with PyNOT.

In case multiple spectra were extracted one has to select the correct one with `--objid <number>` (it will print a table of options). The relevant columns look like this `SPAT0130-SLIT0250-DET01`.

Notes:
* If you want to upload a host spectrum, change the keyword `type` from to `source` to `host` the `data` dictionary.
  
# Photometry

Use [PyNOT](https://github.com/jkrogager/PyNOT) for that. I still need to write the documentation for doing aperture photometry and image subtraction.
