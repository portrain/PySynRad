import math
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

    def initialize(self, resolution, cutoff):
        """
        Initialise the spectrum by creating the normalised SR spectrum (PDF)
        and a discrete random distribution from which the random numbers
        will be generated
        """
        self._x = np.linspace(0.0, cutoff, resolution)
        self._pdf = self._spectrum(self._x)
        self._pdf /= self._pdf.sum()
        self._disc_dist = rv_discrete(name='spectrum',
                                      values=(np.arange(resolution), self._pdf))

    def pdf(self):
        """Return the spectrum"""
        return (self._x, self._pdf)

    def random(self):
        """Generate a random number according to the spectrum PDF"""
        return self._x[self._disc_dist.rvs()]

    def _k53_integral(self, x):
        """The integral from x to infinity over K_5/3"""
        return integrate.quad(self._k53, x, np.inf)[0]

    def _spectrum(self, x):
        """Calculate the value of the spectrum at x=omega/omega_c"""
        v_k53_integral = np.vectorize(self._k53_integral)
        return self._spectrum_norm * x * v_k53_integral(x)
