
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
        self._full_events = settings['full_events']
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

        self._target_zone_enabled = settings['target_zone']['enabled']
        self._target_zone_radius = settings['target_zone']['radius']
        self._target_zone_boundary = settings['target_zone']['boundary']

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


    def _intersect_target_zone(self, vertex, direction):
        """
        Target zone is an z-axis aligned cylinder with an inner and an outer
        radius and a lower and upper boundary. This code intersects a line with
        the cylinder, not a ray! That's ok for the SyncRad Generator, as this
        shouldn't introduce too many false intersections as long as the generation
        is done in a way such that the photons travel towards the IP.
        """

        # calculate slopes
        if math.fabs(direction[2]) > 0.0000000001:
            slope_xz = direction[0] / direction[2]
            slope_yz = direction[1] / direction[2]
        else:
            slope_xz = 0.0
            slope_yz = 0.0

        # calculate the distance from the z-axis (radius) that the ray has at the
        # lower and upper z-boundary of the cylinder.
        def calc_radius2(boundary):
            x_b = slope_xz*(boundary-vertex[2]) + vertex[0]
            y_b = slope_yz*(boundary-vertex[2]) + vertex[1]
            return x_b**2 + y_b**2

        r_low = calc_radius2(self._target_zone_boundary[0])
        r_up  = calc_radius2(self._target_zone_boundary[1])

        # since it is a z-axis aligned cylinder, the radius can simply be compared
        # to the cylinder radii, in order to check for the intersection of the ray.
        radius2 = [self._target_zone_radius[0]**2, self._target_zone_radius[1]**2]
        return ((r_low < radius2[1]) and (r_up  > radius2[0])) or \
               ((r_up  < radius2[1]) and (r_low > radius2[0]))


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

                if num_photons > 0:

                    # calculate critical energy
                    crit_e = self._crit_e_factor * rho_inv

                    # calculate vertex
                    vx = (cx_c*(step.xip+xs)) - (cx_s*step.zip)
                    vy = -(step.yip+ys)
                    vz = -(cx_c*step.zip) - (cx_s*(step.xip+xs))

                    # calculate momentum
                    px_temp = (math.pi - step.xip_prime) + (ch * xs)
                    py_temp = step.yip_prime + (cv * ys)

                    py_temp *= -1.0
                    pz_temp  = -1.0

                    # rotate momentum into Geant4 space
                    px = (cx_c*px_temp) + (cx_s*pz_temp)
                    py = py_temp
                    pz = (cx_c*pz_temp) - (cx_s*px_temp)
                    norm = 1.0/math.sqrt(px**2 + py**2 + pz**2)

                    # if the target zone feature is on, only write events if
                    # the photons will hit the zone.
                    if (not self._target_zone_enabled) or \
                       (self._target_zone_enabled and \
                        self._intersect_target_zone([vx, vy, vz], [px, py, pz])):

                        # if full event writing is turned on, get the energies
                        # for all radiated photons and write them into the
                        # event file
                        if self._full_events:
                            energies = self._spectrum.random(crit_e, num_photons,
                                                             self._energy_cutoff)
                            if len(energies) > 0:
                                evt = hepevt.event(vx, vy, vz)
                                for e in energies:
                                    evt.add(px*e*norm, py*e*norm, pz*e*norm)
                                evt.commit()
                            total_number_photons_cut += len(energies)
                        else:
                            evt = hepevt.event(vx, vy, vz,
                                               num_photons=num_photons,
                                               critical_e=crit_e)
                            evt.add(px*norm, py*norm, pz*norm)
                            evt.commit()

                ys += ystep
            xs += xstep
        output.write(["%f:%i:%i:%e:%e:%e:%e\n"%(step.s0ip,
                                       total_number_photons,
                                       total_number_photons_cut,
                                       step.x, step.y,
                                       step.xp, step.yp)])
