import math
import bisect
from model.region import Region


class Layer(object):
    """
    A layer consists of multiple, non-overlapping regions. Between magnet
    regions there is always a vacuum region. The regions are ordered
    in ascending order of s.
    """
    def __init__(self):
        self._s = []  # left border of regions
        self._regions = []  # list of regions in ascending order of s


    def load(self, filename):
        self._filename = filename
        lattice_file = open(filename, "r")

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
                    vac_region.add(prev_s + prev_l,
                                   math.fabs(s - prev_s - prev_l),
                                   vacuum=True)
                    self._regions.append(vac_region)

                    # start new region
                    current_region = Region()

            # add lattice parameters to region
            current_region.add(s, l,
                               float(tokens[3])/l, # K0
                               float(tokens[4])/l, # K1
                               float(tokens[5])/l, # SK0
                               float(tokens[6])/l, # SK1
                               float(tokens[8]),   # DX
                               float(tokens[9]),   # DY
                               float(tokens[7])    # angle
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


    def write(self, output):
        output_text = ["[%s]"%self._filename]
        for region in self._regions:
            reg_type = "MAG"
            if region.is_vacuum():
                reg_type = "VAC"

            output_text.append("%s %f %f %i\n"%(reg_type,
                                                region.left(),
                                                region.right(),
                                                region.count()))
        output.write(output_text)
