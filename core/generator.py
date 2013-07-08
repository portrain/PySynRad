
import math
import logging.config
from core.settings import Settings
from core.output import Output
from core.orbit import Orbit
from core.twiss import Twiss

logger = logging.getLogger(__name__)


class Generator():
    """
    The main Synchrotron Radiation generator.
    """
    def __init__(self):
        pass

    def initialize(self, lattice):
        self._stop = Settings()['generator']['stepping']['stop']
        self._lattice = lattice
        self._orbit = Orbit()
        self._twiss = Twiss()

        # output
        self._output_orbit = Output('orbit_parameters')
        self._output_twiss = Output('twiss_parameters')
        self._output_orbit.open()
        self._output_twiss.open()
        
    def run(self):

        while self._orbit.valid(self._stop):
            # step the orbit and evolve the twiss parameter
            curr_region = self._lattice.get(self._orbit.s0ip)
            self._orbit.step(curr_region)
            self._twiss.step(self._orbit, curr_region)

            # wite orbit and twiss parameter
            self._orbit.write(self._output_orbit)
            self._twiss.write(self._output_twiss, self._orbit.s0ip)

    def terminate(self):
        self._output_orbit.close()
        self._output_twiss.close()
