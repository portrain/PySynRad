import math
from app.settings import Settings
from model.step import Step

class Orbit():
    """
    The orbit
    """
    def __init__(self):
        pass


    def initialize(self, lattice):
        self._lattice = lattice
        settings = Settings()['generator']['orbit']
        self._start = settings['start']
        self._stop = settings['stop']
        self._nominal_ds = settings['step_size']


    def create_step(self):
        settings = Settings()['generator']['orbit']
        return Step(self._lattice,
                    s0ip=settings['start'],
                    ds=settings['step_size'],
                    s0ip_prime=math.pi,
                    x=settings['offset']['position'],
                    y=0.0,
                    dl=settings['step_size'],
                    xp=-settings['offset']['angle'],
                    yp=0.0,
                    xip_prime=math.pi + settings['offset']['angle'],
                    yip_prime=0.0)


    def valid(self, step):
        # true if this step is valid and not the last step
        return (step.ds < 0.0 and step.s0ip >= self._stop) or \
               (step.ds > 0.0 and step.s0ip <= self._stop)


    def step_ideal_orbit(self, step):
        step.ds = self._nominal_ds
        step.on_boundary = False

        # calculate the distance to the nearest left/right region boundary
        prev_regions = self._lattice.get(step.s0ip)
        smallest_dist = -1.0
        for reg in prev_regions:
            dist = 0.0
            if step.ds < 0.0:
                dist = math.fabs(step.s0ip-reg.left())
            else:
                dist = math.fabs(step.s0ip-reg.right())
            if smallest_dist < 0.0:
                smallest_dist = dist
            elif dist < smallest_dist:
                smallest_dist = dist

        # if the distance is smaller than ds, a magnet<->vacuum boundary
        # will be crossed and ds is adjusted such that the step lies
        # on the boundary
        if (smallest_dist > 0.0) and (smallest_dist < step.ds):
            if self._nominal_ds < 0.0:
                step.ds = -smallest_dist
            else:
                step.ds = smallest_dist
            step.on_boundary = True

        # step the ideal orbit
        step.s0ip += step.ds

        # update the vacuum status
        next_regions = self._lattice.get(step.s0ip)
        step.in_vacuum = True
        for reg in next_regions:
            step.in_vacuum = step.in_vacuum and reg.is_vacuum()


    def step_actual_orbit(self, step):
        # update the curvature
        step.gh = 0.0
        step.gv = 0.0

        regions = self._lattice.get(step.s0ip)
        for iRegion in range(len(regions)):
            region = regions[iRegion]
            if not region.is_vacuum():
                # If the region or the parameter within the region for this
                # layer changed, update the layer's curvature
                curv = step.curvatures[iRegion]
                idx = region.index(step.s0ip)
                if (curv.region != region) or (curv.index != idx):
                    curv.region = region
                    curv.index = idx

                    # magnet displacement
                    mag_x = step.x - region.offset_horz(idx)
                    mag_y = step.y - region.offset_vert(idx)

                    # magnet rotation around s
                    m_s = math.sin(-region.angle(idx))
                    m_c = math.cos(-region.angle(idx))
                    x_tmp = mag_x
                    mag_x = (m_c * x_tmp) - (m_s * mag_y)
                    mag_y = (m_s * x_tmp) + (m_c * mag_y)

                    # calculate curvature
                    curv.gh = region.k0(idx)  + (region.k1(idx) * mag_x) - \
                              (region.sk1(idx) * mag_y)
                    curv.gv = region.sk0(idx) + (region.k1(idx) * mag_y) + \
                              (region.sk1(idx) * mag_x)
                else:
                    # evolve curvature
                    curv.gh += step.dl * ((region.k1(idx) * step.xp) - \
                                          (region.sk1(idx) * step.yp))
                    curv.gv += step.dl * ((region.k1(idx) * step.yp) + \
                                          (region.sk1(idx) * step.xp))
                    step.s0ip_prime -= step.ds * region.k0(idx) * region.length(idx)
    
                step.gh += curv.gh
                step.gv += curv.gv

        
        # calculate actual step length
        if step.in_vacuum:
            step.dl = step.ds / math.cos(step.xp)
        else:
            step.dl = step.ds * (1.0 + (step.gh * step.x))

        # calculate the deviation from the ideal orbit
        step.x += step.dl * step.xp
        step.y += step.dl * step.yip_prime
        step.xip_prime += step.gh * step.dl
        step.yip_prime += step.gv * step.dl

        if not step.in_vacuum:
            step.xp = step.s0ip_prime - step.xip_prime
            step.yp = step.yip_prime
