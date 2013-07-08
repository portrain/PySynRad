
import math
from core.settings import Settings
from core.output import Output


class Twiss():
    """
    The twiss parameters
    """
    def __init__(self):
        settings = Settings()['generator']['twiss_propagation']
        self.alphah = settings['alpha']['horizontal']
        self.alphav = settings['alpha']['vertical']
        self.zetah = math.sqrt(settings['beta']['horizontal'])
        self.zetav = math.sqrt(settings['beta']['vertical'])
        self.zetahp = self.alphah/self.zetah
        self.zetavp = self.alphav/self.zetav
        self.etah = settings['eta']['horizontal']
        self.etav = settings['eta']['vertical']
        self.etahp = settings['eta_derivative']['horizontal']
        self.etavp = settings['eta_derivative']['vertical']
        self.emith = settings['emittance']['horizontal']
        self.emitv = settings['emittance']['vertical']
        self.delta_e = settings['delta_e']

    def beam_size(self):
        hsize_sq = self.emith * self.zetah**2 + self.etah**2 * self.delta_e**2
        vsize_sq = self.emitv * self.zetav**2 + self.etav**2 * self.delta_e**2
        ch = (self.emith * self.zetah * self.zetahp + self.etah * self.etahp * self.delta_e**2)/hsize_sq;
        cv = (self.emitv * self.zetav * self.zetavp + self.etav * self.etavp * self.delta_e**2)/vsize_sq;
        hsize = math.sqrt(hsize_sq)
        vsize = math.sqrt(vsize_sq)
        return hsize, vsize, ch, cv

    def step(self, orbit, region):
        # propagate zeta and eta
        self.zetah += self.zetahp * orbit.dl
        self.zetav += self.zetavp * orbit.dl
        self.etah += self.etahp * orbit.dl
        self.etav += self.etavp * orbit.dl

        # propagate the derivates
        kh = 0.0
        kv = 0.0
        if region.is_vacuum():
            kh = 0.0
            kv = 0.0
        else:
            kh = (-1.0 * region.k1_horz(orbit.s0ip)) - (orbit.gh**2)
            kv = (-1.0 * region.k1_vert(orbit.s0ip)) - (orbit.gv**2)

        zetahpp = (kh * self.zetah) + (1.0/(self.zetah**3))
        self.zetahp += zetahpp * orbit.dl
        zetavpp = (kv * self.zetav) + (1.0/(self.zetav**3))
        self.zetavp += zetavpp * orbit.dl
        etahpp = (kh * self.etah) + orbit.gh
        self.etahp += etahpp * orbit.dl
        etavpp = (kv * self.etav) + orbit.gv
        self.etavp += etavpp * orbit.dl

    def write(self, output, s):
        output.write(["%f:%e:%e:%e:%e:%e:%e\n"%(s,
                                                self.zetahp*self.zetah,
                                                self.zetavp*self.zetav,
                                                self.zetah, self.zetav,
                                                self.etah, self.etav)])
