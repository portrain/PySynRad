
from model.layer import Layer


class Lattice(object):
    """
    The magnetic field lattice. Consists of a list of layers.
    """
    def __init__(self):
        self._layers = []


    def load(self, filenames):
        self._layers = []
        for filename in filenames:
            new_layer = Layer()
            new_layer.load(filename)
            self._layers.append(new_layer)


    def get(self, s):
        return [lay.get(s) for lay in self._layers]


    def count(self):
        return len(self._layers)


    def write(self, output):
        for layer in self._layers:
            layer.write(output)
