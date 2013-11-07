
import math
from app.settings import Settings
from app.hepevt import Hepevt
from core.spectrum import Spectrum

class Photons():
    """
    Integrate over the beam and create the photons
    """
    def __init__(self):
        pass


    def initialize(self, lattice):
        # read settings
        settings = Settings()['generator']['photons']
        self._enabled = settings['enabled']
        self._nth_step = settings['nth_step']
        self._time = settings['time']
        self._energy_cutoff = settings['energy_cutoff']
        self._sigma_h = settings['sigma']['horizontal']
        self._sigma_v = settings['sigma']['vertical']
        self._stepsize_h = 2.0 * self._sigma_h / settings['steps']['horizontal']
        self._stepsize_v = 2.0 * self._sigma_v / settings['steps']['vertical']
        self._crossing_angle = Settings()['machine']['crossing_angle']
        
        self._region_enabled = settings['region']['enabled']
        if settings['region']['range'][0] < settings['region']['range'][1]:
            self._region_left = settings['region']['range'][0]
            self._region_right = settings['region']['range'][1]
        else:
            self._region_left = settings['region']['range'][1]
            self._region_right = settings['region']['range'][0]

        # create synchrotron radiation power spectrum PDF
        self._spectrum = Spectrum()
        self._spectrum.initialize(settings['spectrum']['resolution'],
                                  settings['spectrum']['cutoff'],
                                  settings['spectrum']['seed'],
                                  settings['spectrum']['interpolation'])

        # internal parameters
        self._lattice = lattice
        self._call_count = 0
        self._dl = 0.0

        # internal constants and pre-calculated factors
        self._alpha = 1.0 / 137.035999074
        self._speed_of_light = 2.99792458e8 # [m/s]
        self._hbar = 6.58211928e-25 # [GeV s]
        self._gamma = Settings()['machine']['beam_energy'] / 510.998928e-6
        self._current = Settings()['machine']['beam_current'] * 6.241508e18
        self._num_photon_factor = (5.0 / (2.0*math.sqrt(3))) * \
                                  self._gamma * self._alpha * \
                                  self._current * self._time
        self._crit_e_factor = 3.0 / 2.0 * self._speed_of_light * \
                              self._hbar * (self._gamma**3)


    def create(self, step, beam, output, hepevt):
        if not self._enabled:
            return

        # accumulate steps only inside magnets and, if enabled,
        # inside the region
        if (not step.in_vacuum) and \
           (not self._region_enabled or \
            (self._region_enabled and \
             step.s0ip >= self._region_left and step.s0ip <= self._region_right)):
            self._dl += step.dl
            self._call_count += 1

        # radiate photons if the n-th step is reached,
        # the current step is on a magnet to vacuum boundary,
        # or the region is enabled and the step leaves the region
        if (self._call_count >= self._nth_step) or \
           (self._call_count > 0 and step.on_boundary) or \
           (self._region_enabled and self._call_count > 0 and step.ds < 0.0 and \
            step.s0ip <= self._region_left) or \
           (self._region_enabled and self._call_count > 0 and step.ds > 0.0 and \
            step.s0ip >= self._region_right):
            self._integrate_beam(math.fabs(self._dl),
                                 step, beam,
                                 output, hepevt)
            self._dl = 0.0
            self._call_count = 0


    def write_spectrum(self, output):
        self._spectrum.write(output)


    def _integrate_beam(self, dl, step, beam, output, hepevt):
        """
        integrate over the beam profile
        """
        total_number_photons = 0
        total_number_photons_cut = 0

        k1s = []
        for region in self._lattice.get(step.s0ip):
            idx = region.index(step.s0ip)
            k1s.append([region.k1(idx), region.sk1(idx)])

        hsize, vsize, ch, cv = beam.size()
        prob_norm_1 = 1.0 / (2.506628 * hsize * vsize)
        prob_norm_2 = 1.0 / (2.0*math.pi * hsize * vsize)
        weight_factor = self._stepsize_h * self._stepsize_v * hsize * vsize
        xstep = self._stepsize_h * hsize
        ystep = self._stepsize_v * vsize
        xs_max = self._sigma_h * hsize
        ys_max = self._sigma_v * vsize

        cx_s = math.sin(self._crossing_angle)
        cx_c = math.cos(self._crossing_angle)

        xs = -1.0 * self._sigma_h * hsize + 0.5*xstep
        while xs <= xs_max:
            ys = -1.0 * self._sigma_v * vsize + 0.5*ystep
            while ys <= ys_max:
                # calculate local radius
                local_gh = step.gh
                local_gv = step.gv
                for k1 in k1s:
                    local_gh += (k1[0] * xs) - (k1[1] * ys)
                    local_gv += (k1[0] * ys) + (k1[1] * xs)
                rho_inv = math.sqrt(local_gh**2 + local_gv**2)

                # calculate weight
                prob = 0.0
                nsigh = xs / hsize
                nsigv = ys / vsize

                # beam profile. Either Talman tails or Gaussian
                if (math.fabs(nsigv) > 5.0) and (beam.emitv / beam.emith < 0.2):
                    prob = prob_norm_1 * math.exp(-0.5*nsigh**2) * \
                                         math.exp(-7.4 -1.2*math.fabs(nsigv))
                else:
                    prob = prob_norm_2 * math.exp(-0.5*(nsigh**2 + nsigv**2))
                weight = prob * weight_factor

                # calculate number of radiated photons
                num_photons = int(self._num_photon_factor * rho_inv * weight * dl)
                total_number_photons += num_photons

                # get the energies for all radiated photons
                if num_photons > 0:
                    crit_e = self._crit_e_factor * rho_inv
                    energies = self._spectrum.random(crit_e, num_photons,
                                                     self._energy_cutoff)

                    # write photons into the event file
                    if len(energies) > 0:
                        vx = -cx_s*step.s0ip + cx_c*(step.x+xs)
                        vy = step.y+ys
                        vz = -cx_c*step.s0ip - cx_s*(step.x+xs)
                        px = cx_s*(step.s0ip-step.ds) + cx_c*step.xp*step.ds
                        py = step.yp*step.ds
                        pz = cx_c*(step.s0ip-step.ds) - cx_s*step.xp*step.ds
                        norm = 1.0/math.sqrt(px**2 + py**2 + pz**2)
                        evt = hepevt.event(vx, vy, vz)
                        for e in energies:
                            evt.add(px*e*norm, py*e*norm, pz*e*norm)
                        evt.commit()
                    total_number_photons_cut += len(energies)

                ys += ystep
            xs += xstep
        output.write(["%f:%i:%i:%e:%e:%e:%e\n"%(step.s0ip,
                                       total_number_photons,
                                       total_number_photons_cut,
                                       step.x, step.y,
                                       step.xp, step.yp)])
