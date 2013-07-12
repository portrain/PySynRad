
import math
from core.settings import Settings
from core.output import Output


class RegionCache():
    """
    Stores the data for the current step in a single region.
    """
    def __init__(self):
        self.region = None
        self.index = -1
        self.gh = 0.0
        self.gv = 0.0


class Orbit():
    """
    The orbit
    """
    def __init__(self, lattice_layers):
        # read settings
        settings = Settings()['generator']['stepping']

        # ideal central orbit
        self.s0ip = settings['start']  # ideal position (s, x, z)
        self.nominal_ds = settings['step_size'] # ideal (specified) step size
        self.ds = settings['step_size'] # current step size
        self.s0ip_prime = math.pi # ideal angle

        # actual orbit
        self.x = settings['offset']['position'] # position deviation from ideal orbit
        self.y = 0.0
        self.dl = settings['step_size'] # step length along actual orbit
        self.xp = -settings['offset']['angle'] # angle deviation from ideal orbit
        self.yp = 0.0
        self.xip_prime = math.pi + settings['offset']['angle'] # actual orbit angles
        self.yip_prime = 0.0

        # curvature at the current step
        self.gh = 0.0
        self.gv = 0.0

        # list of the current region and the index within the region.
        # Used to check if a region or the index has changed.
        self._region_cache = [RegionCache()]*len(lattice_layers)


    def step(self, regions):
        # check if the step is in vacuum
        in_vacuum = True
        for region in regions:
            in_vacuum = in_vacuum and region.is_vacuum()

        # update the curvature
        self.gh = 0.0
        self.gv = 0.0
        for ireg in range(len(regions)):
            region = regions[ireg]
            region_c = self._region_cache[ireg]
            index = region.index(self.s0ip)

            if not region.is_vacuum():
                if (region_c.region != region) or (region_c.index != index):
                    region_c.region = region
                    region_c.index = index

                    # magnet displacement
                    mag_x = self.x - region.offset_horz(index)
                    mag_y = self.y - region.offset_vert(index)

                    # magnet rotation around s
                    m_s = math.sin(-region.angle(index))
                    m_c = math.cos(-region.angle(index))
                    x_tmp = mag_x
                    mag_x = (m_c * x_tmp) - (m_s * mag_y)
                    mag_y = (m_s * x_tmp) + (m_c * mag_y)

                    # calculate curvature
                    region_c.gh = region.k0(index)  + (region.k1(index) * mag_x) - (region.sk1(index) * mag_y)
                    region_c.gv = region.sk0(index) + (region.k1(index) * mag_y) + (region.sk1(index) * mag_x)
                else:
                    # evolve curvature
                    region_c.gh += self.dl * ((region.k1(index) * self.xp) - (region.sk1(index) * self.yp))
                    region_c.gv += self.dl * ((region.k1(index) * self.yp) + (region.sk1(index) * self.xp))
                    self.s0ip_prime -= self.ds * region.k0(index) * region.length(index)
    
                self.gh += region_c.gh
                self.gv += region_c.gv

        # step the ideal orbit
        self.s0ip += self.ds

        # calculate actual step length
        if in_vacuum:
            self.dl = self.ds / math.cos(self.xp)
        else:
            self.dl = self.ds * (1.0 + (self.gh * self.x))

        # calculate the actual orbit + deviation from ideal orbit
        self.x += self.dl * self.xp
        self.y += self.dl * self.yip_prime
        self.xip_prime += self.gh * self.dl
        self.yip_prime += self.gv * self.dl

        if not in_vacuum:
            self.xp = self.s0ip_prime - self.xip_prime
            self.yp = self.yip_prime


    def valid(self, stop):
        # return true if this step is valid and not the last step
        return (self.ds < 0.0 and self.s0ip >= stop) or \
               (self.ds > 0.0 and self.s0ip <= stop)

    def write(self, output):
        output.write(["%f:%e:%e\n"%(self.s0ip, self.x, self.y,)])
