
import math
from app.settings import Settings
from core.spectrum import Spectrum

class Photons():
    """
    Integrate over the beam and create the photons
    """
    def __init__(self):
        pass


    def initialize(self):
        # read settings
        settings = Settings()['generator']['photons']
        self._enabled = settings['enabled']
        self._nth_step = settings['nth_step']
        self._time = settings['time']
        self._sigma_h = settings['sigma']['horizontal']
        self._sigma_v = settings['sigma']['vertical']
        self._stepsize_h = 2.0 * self._sigma_h / settings['steps']['horizontal']
        self._stepsize_v = 2.0 * self._sigma_v / settings['steps']['vertical']

        # create synchrotron radiation power spectrum PDF
        self._spectrum = Spectrum()
        self._spectrum.initialize(settings['spectrum']['resolution'],
                                  settings['spectrum']['cutoff'])

        # internal parameters
        self._call_count = 0
        self._dl = 0.0


    def create(self, step, beam):
        # accumulate steps only inside magnets
        if not step.in_vacuum:
            self._dl += orbit.dl
            self._call_count += 1

        # radiate photons if the n-th step is reached
        # or the current step is on a magnet to vacuum boundary.
        if (self._call_count >= self._nth_step) or \
           (self._call_count > 0 and step.on_boundary):


            self._dl = 0.0
            self._call_count = 0
