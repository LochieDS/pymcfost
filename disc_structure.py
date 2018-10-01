import astropy.io.fits as fits
import matplotlib.pyplot as plt
import numpy as np
import os

from parameters import McfostParams, find_parameter_file


class McfostDisc:

    def __init__(self, dir=None, **kwargs):
        # Correct path if needed
        dir = os.path.normpath(os.path.expanduser(dir))
        if (dir[-9:] != "data_disk"):
            dir = os.path.join(dir,"data_disk")
        self.dir = dir

        # Search for parameter file
        para_file = find_parameter_file(dir)

        # Read parameter file
        self.P = McfostParams(para_file)

        # Read model results
        self._read(**kwargs)

    def _read(self):
        # Read grid file
        try:
            hdu = fits.open(self.dir+"/grid.fits.gz")
        except OSError:
            print('cannot open grid.fits.gz')
        self.grid = hdu[0].data
        hdu.close()

        # Read gas density file
        try:
            hdu = fits.open(self.dir+"/gas_density.fits.gz")
        except OSError:
            print('cannot open gas_density.fits.gz')
        self.gas_density = hdu[0].data
        hdu.close()

        # Read volume file
        try:
            hdu = fits.open(self.dir+"/volume.fits.gz")
        except OSError:
            print('cannot open volume.fits.gz')
        self.volume = hdu[0].data
        hdu.close()

    def r(self):
        if (self.grid.ndim > 2):
            return self.grid[0,0,:,:]
        else:
            return np.sqrt(self.grid[0,:]**2 + self.grid[1,:]**2)

    def z(self):
        if (self.grid.ndim > 2):
            return self.grid[1,0,:,:]
        else:
            return self.grid[2,:]

    def add_spiral(self, a=3, sigma=10, f=1, theta0=0, rmin=None, rmax=None, n_az=None):
        """ Add a geometrucal spiral on a 2D (or 3D) mcfost density grid
        and return a 3D array which can be directly written as a fits
        file for mcfost to read

        geometrical spiral r = a (theta - theta0)
        surface density is mutiply by f at the crest of the spiral
        the spiral has a Gaussin profil in (x,y) with sigma given in au
        """

        if (self.grid.ndim <= 2):
            ValueError("Can only add a spiral on a cylindrical or spherical grid")

        if (n_az is None):
            n_az = self.grid.shape[1]
        phi = np.linspace(0,2*np.pi,n_az,endpoint=False)

        print(self.gas_density.shape)

        r = self.grid[0,0,0,:]

        if rmin is None:
            rmin = r.min()
        if rmax is None:
            rmax = r.max()

        x = r[np.newaxis,:] * np.cos(phi[:,np.newaxis])
        y = r[np.newaxis,:] * np.sin(phi[:,np.newaxis])

        # Just to test
        #x = np.linspace(-100,100,500)
        #x, y = np.meshgrid(x,x)
        #r = np.sqrt(x**2 + y**2) # we recalcule in preparation for other types of grid

        # rc=50, hc=0.15, alpha=1.5, beta=0.25
        # theta_c = 0.
        # theta = theta_c + np.sign(r - rc)/hc * \
        #        ((r/rc)**(1+beta) * (1/(1+beta) - 1/(1-alpha + beta) * (r/rc)**(-alpha)) \
        #         - 1/(1+beta) - 1/(1-alpha + beta))

        r_spiral = np.geomspace(rmin,rmax,num=5000)
        theta = r_spiral/a + theta0

        x_spiral = r_spiral * np.cos(theta)
        y_spiral = r_spiral * np.sin(theta)

        correct = np.ones(x.shape)

        # This is really badly implemented, but fast enough that we don't care
        sigma2 = sigma**2
        for i in range(x.shape[0]):
            for j in range(x.shape[1]):
                d2 = np.min( (x_spiral - x[i,j])**2 + (y_spiral - y[i,j])**2 )
                correct[i,j] += f * np.exp(-0.5 * d2/sigma2)


        return self.gas_density[np.newaxis,:,:] * correct[:,np.newaxis,:]
