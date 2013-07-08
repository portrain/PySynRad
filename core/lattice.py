
import os
import math
import bisect
from core.settings import Settings
from core.output import Output


class Region():
    """
    A region contains either vacuum or a list of hard edge modeled
    lattice parameters
    """
    def __init__(self):
        self._s = []
        self._params = []
        self._smin = 0.0
        self._smax = 0.0

    def add(self, s, l, k0=0.0, k1=0.0, vacuum=False):
        if len(self._s) == 0:
            self._smin = s
            self._smax = s + l
        else:
            if s < self._smin:
                self._smin = s
            elif s + l > self._smax:
                self._smax = s + l
        if not vacuum:
            idx = bisect.bisect_left(self._s, s)
            self._s.insert(idx, s)
            self._params.insert(idx, [k0, k1])

    def is_vacuum(self):
        return len(self._params) == 0

    def left(self):
        return self._smin

    def right(self):
        return self._smax

    def count(self):
        return len(self._params)

    def k0_horz(self, s):
        return self._return_param(s, 0, 0.0)

    def k0_vert(self, s):
        return -1.0 * self._return_param(s, 0, 0.0)

    def k1_horz(self, s):
        return self._return_param(s, 1, 0.0)

    def k1_vert(self, s):
        return -1.0 * self._return_param(s, 1, 0.0)

    def _return_param(self, s, param_index, default):
        idx = bisect.bisect_left(self._s, s)-1
        if idx != len(self._s):
            return self._params[idx][param_index]
        else:
            return default


class Lattice():
    """
    The magnetic field lattice. Consists of a list of regions.
    """
    def __init__(self):
        self._s = []  # left border of regions
        self._regions = []  # list of regions in ascending order of s

    def load(self):
        file_path = os.path.join(Settings()['application']['conf_path'],
                                 Settings()['machine']['lattice'])
        lattice_file = open(file_path, "r")

        current_region = Region()
        prev_s = 0.0
        prev_l = 0.0
        for line in lattice_file:
            tokens = line.split()
            s = float(tokens[1])
            l = float(tokens[2])

            # check if the previous region has to be closed.
            if prev_l > 0.0:
                if math.fabs(prev_s + prev_l - s) > 0.000000000001:
                    # close previous region
                    self._s.append(current_region.left())
                    self._regions.append(current_region)

                    # add vacuum region as a bridge between two
                    # lattice regions
                    vac_region = Region()
                    self._s.append(prev_s + prev_l)
                    vac_region.add(prev_s + prev_l, math.fabs(s - prev_s - prev_l),
                                   vacuum=True)
                    self._regions.append(vac_region)

                    # start new region
                    current_region = Region()

            # add lattice parameters to region
            current_region.add(s, l,
                               float(tokens[3])/l, # K0
                               float(tokens[4])/l  # K1
                               )

            prev_s = s
            prev_l = l
        # store last region
        self._s.append(current_region.left())
        self._regions.append(current_region)
        lattice_file.close()

    def get(self, s):
        # if s is outside the leftmost and rightmost region,
        # return vacuum region
        if (s < self._regions[0].left()) or \
           (s > self._regions[len(self._regions)-1].right()):
           return Region()
        return self._regions[bisect.bisect_left(self._s, s)-1]

    def write_regions(self):
        reg_out = Output('regions')
        reg_out.open()
        for region in self._regions:
            reg_type = "MAG"
            if region.is_vacuum():
                reg_type = "VAC"
            reg_out.write(["%s %f %f %i\n"%(reg_type,
                                           region.left(),
                                           region.right(),
                                           region.count())])
        reg_out.close()
