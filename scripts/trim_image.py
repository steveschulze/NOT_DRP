import astropy.io.fits as fits
import click
import os



@click.command()
@click.argument('images', nargs=-1)
def main(images):
    for image in images:
        dest_fname = os.path.basename(image)
        hdu = fits.open(image, mode='update')

        data = hdu[1].data
        print(data.shape)
        new_data = data[0:1800,600:1700]
        print(new_data.shape)
        hdu[1].data = new_data
        hdu.flush()
        hdu.close()

        



if __name__ == '__main__':
    main()
