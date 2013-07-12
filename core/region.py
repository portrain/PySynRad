import math
import bisect

class Region():
    """
    A region contains either vacuum or a list of hard edge modeled
    lattice parameters.
    """
    def __init__(self):
        self._s = []
        self._params = []
        self._smin = 0.0
        self._smax = 0.0

    def add(self, s, l, k0=0.0, k1=0.0, sk0=0.0, sk1=0.0,
            dh=0.0, dv=0.0, angle=0.0, vacuum=False):
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
            self._params.insert(idx, [k0, k1, sk0, sk1, dh, dv, angle, l])

    def is_vacuum(self):
        return len(self._params) == 0

    def left(self):
        return self._smin

    def right(self):
        return self._smax

    def index(self, s):
        return bisect.bisect_left(self._s, s)-1

    def count(self):
        return len(self._params)

    def k0(self, index):
        return self._return_param(index, 0, 0.0)

    def k1(self, index):
        return self._return_param(index, 1, 0.0)

    def sk0(self, index):
        return self._return_param(index, 2, 0.0)

    def sk1(self, index):
        return self._return_param(index, 3, 0.0)

    def offset_horz(self, index):
        return self._return_param(index, 4, 0.0)

    def offset_vert(self, index):
        return self._return_param(index, 5, 0.0)

    def angle(self, index):
        return math.radians(self._return_param(index, 6, 0.0))

    def length(self, index):
        return math.fabs(self._return_param(index, 7, 0.0))

    def _return_param(self, index, param_index, default):
        if len(self._params) > 0:
            if index != len(self._params):
                return self._params[index][param_index]
            else:
                return default
        else:
            return default
