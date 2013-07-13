from model.curvature import Curvature


class Step(object):

    def __init__(self, lattice,
                       s0ip=0.0, ds=0.0, s0ip_prime=0.0,
                       x=0.0, y=0.0, dl=0.0, xp=0.0, yp=0.0,
                       xip_prime=0.0, yip_prime=0.0):
        # ideal central orbit
        self.s0ip = s0ip # ideal s position 
        self.ds = ds # current step size (is dynamic at magnet borders)
        self.s0ip_prime = s0ip_prime # ideal angle

        # actual orbit
        self.x = x # position deviation from ideal orbit
        self.y = y
        self.dl = dl # step length along actual orbit
        self.xp = xp # angle deviation from ideal orbit
        self.yp = yp
        self.xip_prime = xip_prime # actual orbit angles
        self.yip_prime = yip_prime

        # total curvature
        self.gh = 0.0
        self.gv = 0.0

        # status
        self.in_vacuum = True
        self.on_boundary = False

        # create a curvature object for each layer in the lattice at s0ip
        self.curvatures = [Curvature()]*lattice.count()


    def write(self, output):
        output.write(["%f:%e:%e\n"%(self.s0ip, self.x, self.y)])
