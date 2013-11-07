import math
from app.settings import Settings


class Photon():

    def __init__(self, px, py, pz):
        self._px = px
        self._py = py
        self._pz = pz

    def momentum(self):
        return self._px, self._py, self._pz


class Event():

    def __init__(self, x, y, z, num_photons, critical_e, hepevt):
        """
        x,y,z in metres
        """
        self._hepevt = hepevt
        self._num_photons = num_photons
        self._critical_e = critical_e
        self._particles = []
        self._x = x
        self._y = y
        self._z = z

    def add(self, px, py, pz):
        self._particles.append(Photon(px, py, pz))

    def commit(self):
        self._hepevt.write(self)

    def particles(self):
        return self._particles

    def position(self):
        return self._x, self._y, self._z

    def number_photons(self):
        return self._num_photons

    def critical_energy(self):
        return self._critical_e

    def count(self):
        return len(self._particles)



class Hepevt():

    def __init__(self):
        settings = Settings()['application']['output']['events']
        self._enabled = settings['enabled']
        self._filename = settings['filename']
        self._file = None


    def open(self):
        if self._enabled:
            self._file = open(self._filename, "w")
            self._evt_count = 0


    def event(self, x, y, z, num_photons=None, critical_e=None):
        return Event(x, y, z, num_photons, critical_e, self)


    def write(self, event):
        if self._file == None:
            return

        # header
        extra = ""
        if event.number_photons() != None:
            extra += " %i"%event.number_photons()
        if event.critical_energy() != None:
            extra += " %.6e"%event.critical_energy()
        self._file.write("%i"%event.count() +\
                         " %.6e %.6e %.6e"%(event.position()) +\
                         "%s\n"%extra)

        # body
        for particle in event.particles():
            self._file.write("%.6e %.6e %.6e\n"%(particle.momentum()))

        self._evt_count += 1


    def close(self):
        if self._file != None:
            self._file.close()
