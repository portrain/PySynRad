import math
import random
import bisect
import numpy as np
import scipy as sp
from scipy import integrate
from scipy.stats import rv_discrete


class Spectrum():
    """
    This class provides the normalised spectrum for synchrotron radiation in
    units of omage/omega_c. It also offers a method to produce random numbers
    according to the spectrum PDF.

    Formulas are taken from:
    G. J. Roy, A new method for the simulation of synchrotron radiation
               in particle tracking codes, Nucl. Inst. Meth. A298 (1990) 128-133
    """
    def __init__(self):
        """
        Define the modified Bessel function of order 5/3 and
        set internal constants.
        """
        self._k53 = lambda ksi: sp.special.kv(5.0/3.0,ksi)
        self._spectrum_norm = (9.0*math.sqrt(3.0)) / (8.0 * math.pi)


    def initialize(self, resolution, cutoff, seed=1817, interpolate=False):
        """
        Initialise the spectrum by creating the normalised SR spectrum (PDF)
        and a discrete random distribution from which the random numbers
        will be generated
        """
        np.random.seed(seed)
        self._resolution = resolution
        self._interpolate = interpolate
        self._x = np.linspace(0.0, cutoff, resolution)
        self._pdf = self._spectrum(self._x)
        self._pdf /= self._pdf.sum()
        self._disc_dist = rv_discrete(name='spectrum',
                                      values=(self._x, self._pdf))

        # create the lookup table
        self._lut_x = np.linspace(0.0, 1.0, resolution)
        self._lut_y = self._disc_dist.ppf(self._lut_x)


    def pdf(self):
        """Return the spectrum"""
        return (self._x, self._pdf)


    def random(self, critical_e, number=1, cutoff_e=0.0):
        """
        Generate a list of random energy values according to the spectrum PDF
        """
        result = []
        cut = self._cutoff_value(critical_e, cutoff_e)
        rnd_values = np.random.random(number)

        if not self._interpolate:
            for rnd in rnd_values:
                if rnd < cut:
                    continue
                result.append(critical_e * \
                              self._lut_y[int(rnd * self._resolution)])
        else:
            for rnd in rnd_values:
                if rnd < cut:
                    continue

                # find left and right bin
                left = int(rnd * self._resolution)
                right = left+1
                if right >= len(self._lut_x):
                    right = left
                    left = right-1

                # perform linear interpolation
                result.append(critical_e * \
                              np.interp(rnd,
                                        [self._lut_x[left], self._lut_x[right]],
                                        [self._lut_y[left], self._lut_y[right]]))

        return result


    def write(self, output):
        output.write([str(self._resolution)+"\n"])
        output.write(["%f\n"%y for y in self._lut_y])


    def _k53_integral(self, x):
        """The integral from x to infinity over K_5/3"""
        return integrate.quad(self._k53, x, np.inf)[0]


    def _spectrum(self, x):
        """Calculate the value of the spectrum at x=omega/omega_c"""
        v_k53_integral = np.vectorize(self._k53_integral)
        return self._spectrum_norm * x * v_k53_integral(x)


    def _cutoff_value(self, critical_e, cutoff_e):
        search_value = cutoff_e / critical_e
        i = bisect.bisect_right(self._lut_y, search_value)
        if i > 0:
            return self._lut_x[i-1]
        else:
            return self._lut_x[0]
