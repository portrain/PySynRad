
import math
from core.settings import Settings
from core.output import Output


class Orbit():
    """
    The orbit
    """
    def __init__(self):
        # read settings
        settings = Settings()['generator']['stepping']

        # ideal central orbit
        self.s0ip = settings['start']  # ideal position (s, x, z)
        self.x0ip = 0.0
        self.z0ip = 0.0
        self.nominal_ds = settings['step_size'] # ideal (specified) step size
        self.ds = settings['step_size'] # current step size
        self.s0ip_prime = math.pi # ideal angle

        # actual orbit
        self.x = settings['offset']['position'] # position deviation from ideal orbit
        self.y = 0.0
        self.dl = settings['step_size'] # step length along actual orbit
        self.xp = -settings['offset']['angle'] # angle deviation from ideal orbit
        self.yp = 0.0
        self.xip = settings['offset']['position'] # actual orbit position
        self.yip = 0.0
        self.zip = -settings['start']
        self.lip = settings['start']
        self.xip_prime = math.pi + settings['offset']['angle'] # actual orbit angles
        self.yip_prime = 0.0

        # curvature at this step
        self.gh = 0.0
        self.gv = 0.0

    def step(self, region):
        # step the ideal orbit first
        self.s0ip += self.ds
        self.x0ip += self.ds * math.sin(self.s0ip_prime)
        self.z0ip += self.ds * math.cos(self.s0ip_prime)

        # calculate actual step length
        if region.is_vacuum():
            self.dl = self.ds / math.cos(self.xp)
        else:
            self.dl = self.ds * (1.0 + (self.gh * self.x))

        # calculate the actual orbit + deviation from ideal orbit
        self.lip += self.dl
        self.xip += self.dl * math.sin(self.xip_prime)
        self.zip += self.dl * math.cos(self.xip_prime)
        self.yip += self.dl * self.yip_prime
        self.x += self.dl * self.xp
        self.y += self.dl * self.yip_prime

        # step the angles
        if not region.is_vacuum():
            self.xip_prime += self.gh * self.dl
            self.yip_prime += self.gv * self.dl
            self.gh += self.xp * self.dl * region.k1_horz(self.s0ip)
            self.gv += self.yp * self.dl * region.k1_vert(self.s0ip)

            self.s0ip_prime += self.ds * region.k0_horz(self.s0ip)
            self.xp = self.s0ip_prime - self.xip_prime
            self.yp = self.yip_prime

        # adjust ds
        #if st.ds < 0.0 and ((step.region().region_smin - st.s0ip) > st.ds):
        #    new_ds = step.region().region_smin - st.s0ip - 0.000001
        #    if math.fabs(new_ds) >= 0.000000001:
        #        st.ds = new_ds
        #elif st.ds > 0.0 and ((step.region().region_smax - st.s0ip) < st.ds):
        #    new_ds = step.region().region_smax - st.s0ip + 0.000001
        #    if math.fabs(new_ds) >= 0.000000001:
        #        st.ds = new_ds

        # update the curvature
        if region.is_vacuum():
            self.gh = 0.0
            self.gv = 0.0
        else:
            self.gh = region.k1_horz(self.s0ip) * self.x + region.k0_horz(self.s0ip)
            self.gv = region.k1_vert(self.s0ip) * self.y + region.k0_vert(self.s0ip)

    def valid(self, stop):
        # return true if this step is valid and not the last step
        return (self.ds < 0.0 and self.s0ip >= stop) or \
               (self.ds > 0.0 and self.s0ip <= stop)

    def write(self, output):
        output.write(["%f:%e:%e:%e:%e:%e:%e:%e:%e\n"%(self.s0ip,
                                                      self.x0ip,
                                                      self.z0ip,
                                                      self.x, self.y,
                                                      self.lip,
                                                      self.xip,
                                                      self.zip,
                                                      self.yip)])
