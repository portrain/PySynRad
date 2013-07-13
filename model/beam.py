

class Beam(object):
    """
    Beam
    """
    def __init__(self, alphah=0.0, alphav=0.0, zetah=0.0, zetav=0.0,
                 etah=0.0, etav=0.0, etahp=0.0, etavp=0.0, emith=0.0, emitv=0.0):
        self.alphah = alphah # twiss parameters
        self.alphav = alphav
        self.zetah = zetah
        self.zetav = zetav
        self.zetahp = self.alphah / self.zetah
        self.zetavp = self.alphav / self.zetav
        self.etah = etah
        self.etav = etav
        self.etahp = etahp
        self.etavp = etavp
        self.emith = emith # emittance
        self.emitv = emitv


    def size(self):
        hsize_sq = self.emith * self.zetah**2 + self.etah**2 * self.delta_e**2
        vsize_sq = self.emitv * self.zetav**2 + self.etav**2 * self.delta_e**2
        ch = (self.emith * self.zetah * self.zetahp + \
              self.etah * self.etahp * self.delta_e**2)/hsize_sq;
        cv = (self.emitv * self.zetav * self.zetavp + \
              self.etav * self.etavp * self.delta_e**2)/vsize_sq;
        hsize = math.sqrt(hsize_sq)
        vsize = math.sqrt(vsize_sq)
        return hsize, vsize, ch, cv


    def write(self, step, output):
        output.write(["%f:%e:%e:%e:%e:%e:%e\n"%(step.s0ip,
                                                self.zetahp*self.zetah,
                                                self.zetavp*self.zetav,
                                                self.zetah, self.zetav,
                                                self.etah, self.etav)])
