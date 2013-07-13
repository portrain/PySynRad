import math
from app.settings import Settings
from model.beam import Beam

class Twiss():
    """
    The twiss parameters
    """
    def __init__(self):
        pass


    def initialize(self, lattice):
        self._lattice = lattice
        settings = Settings()['generator']['twiss']
        self._delta_e = settings['delta_e']


    def create_beam(self):
        settings = Settings()['generator']['twiss']
        return Beam(alphah=settings['alpha']['horizontal'],
                    alphav=settings['alpha']['vertical'],
                    zetah=math.sqrt(settings['beta']['horizontal']),
                    zetav=math.sqrt(settings['beta']['vertical']),
                    etah=settings['eta']['horizontal'],
                    etav=settings['eta']['vertical'],
                    etahp=settings['eta_derivative']['horizontal'],
                    etavp=settings['eta_derivative']['vertical'],
                    emith=settings['emittance']['horizontal'],
                    emitv=settings['emittance']['vertical'])


    def evolve(self, step, beam):
        # propagate zeta and eta
        beam.zetah += beam.zetahp * step.dl
        beam.zetav += beam.zetavp * step.dl
        beam.etah += beam.etahp * step.dl
        beam.etav += beam.etavp * step.dl

        # propagate the derivatives
        kh = 0.0
        kv = 0.0
        for region in self._lattice.get(step.s0ip):
            if not region.is_vacuum():
                idx = region.index(step.s0ip)
                kh += region.k1(idx)
                kv -= region.k1(idx)
        if not step.in_vacuum:
            kh = (-1.0 * kh) - (step.gh**2)
            kv = (-1.0 * kv) - (step.gv**2)

        zetahpp = (kh * beam.zetah) + (1.0/(beam.zetah**3))
        beam.zetahp += zetahpp * step.dl
        zetavpp = (kv * beam.zetav) + (1.0/(beam.zetav**3))
        beam.zetavp += zetavpp * step.dl
        etahpp = (kh * beam.etah) + step.gh
        beam.etahp += etahpp * step.dl
        etavpp = (kv * beam.etav) - step.gv
        beam.etavp += etavpp * step.dl
