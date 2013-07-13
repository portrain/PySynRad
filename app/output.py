
from app.settings import Settings

class Output(object):
    """
    The text file output class
    """
    def __init__(self, name):
        settings = Settings()['application']['output'][name]
        self._enabled = settings['enabled']
        self._nth_step = int(settings['nth_step'])
        self._filename = settings['filename']
        self._file = None
        self._calls = 0

    def open(self):
        if self._enabled:
            self._file = open(self._filename, "w")

    def write(self, data=[]):
        if self._file != None:
            self._calls += 1
            if self._calls%self._nth_step == 0:
                for line in data:
                    self._file.write(line)

    def close(self):
        if self._file != None:
            self._file.close()
