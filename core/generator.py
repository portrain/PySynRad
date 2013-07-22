import os
import math
import logging.config
from progressbar import ProgressBar, Bar, Percentage, ETA
from app.settings import Settings
from app.output import Output
from core.lattice import Lattice
from core.orbit import Orbit
from core.twiss import Twiss
from core.photons import Photons

logger = logging.getLogger(__name__)


class Generator():
    """
    The main Synchrotron Radiation generator.
    """
    def __init__(self):
        self._lattice = Lattice()
        self._orbit = Orbit()
        self._twiss = Twiss()
        self._photons = Photons()


    def initialize(self):
        # get settings
        self._start = Settings()['generator']['orbit']['start']
        self._stop = Settings()['generator']['orbit']['stop']

        # load the lattice
        self._lattice.load([os.path.join(Settings()['application']['conf_path'],
                            fname) for fname in Settings()['machine']['lattice']])

        # initialise the sub-systems
        self._orbit.initialize(self._lattice)
        self._twiss.initialize(self._lattice)
        self._photons.initialize(self._lattice)
        
        # initialise step and beam
        self._step = self._orbit.create_step()
        self._beam = self._twiss.create_beam()

        # output
        self._output_lattice = Output('regions')
        self._output_orbit = Output('orbit_parameters')
        self._output_twiss = Output('twiss_parameters')
        self._output_num_photons = Output('radiated_number_photons')
        self._output_lattice.open()
        self._output_orbit.open()
        self._output_twiss.open()
        self._output_num_photons.open()


    def run(self):
        # write lattice
        self._lattice.write(self._output_lattice)

        # progress bar
        progress_ds = 0.0
        progress = ProgressBar(widgets=['Stepping: ', Percentage(),
                                        ' ', Bar(), ' ', ETA()],
                               maxval=math.fabs(self._stop - self._start)).start()

        # first ideal orbit step
        self._orbit.step_ideal_orbit(self._step)

        # step through the lattice until the stop point is reached
        while self._orbit.valid(self._step):

            # step the actual orbit and evolve the twiss parameters
            self._orbit.step_actual_orbit(self._step)
            self._twiss.evolve(self._step, self._beam)

            # integrate over the beam profile and create the photons
            sr_photons = self._photons.create(self._step, self._beam,
                                              self._output_num_photons)

            # write orbit and twiss parameters to file
            self._step.write(self._output_orbit)
            self._beam.write(self._step, self._output_twiss)

            # write the photons into an hepevt file
            # self._hepevt.write(sr_photons)

            # update progress bar
            progress_ds += math.fabs(self._step.ds)
            progress.update(progress_ds)

            # next ideal orbit step
            self._orbit.step_ideal_orbit(self._step)

        progress.finish()


    def terminate(self):
        self._output_lattice.close()
        self._output_orbit.close()
        self._output_twiss.close()
        self._output_num_photons.close()
