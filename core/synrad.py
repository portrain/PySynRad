
import logging.config
import argparse
from core import settings
from core.lattice import Lattice
from core.generator import Generator


def main():
    # parse the command line arguments
    parser = argparse.ArgumentParser(prog='pysynrad',
                                     description='Synchrotron radiation generator')
    parser.add_argument('<config_file>', action='store',
                        help='Path to configuration file')
    args = vars(parser.parse_args())
    conf_path = args['<config_file>']

    # load the main configuration file
    settings.read(conf_path)

    # set the global logging settings and level
    logging.config.dictConfig(settings.Settings()['application']['logging'])


    #----------------------------------------------------------
    # create and load the lattice
    lattice = Lattice()
    lattice.load()
    lattice.write_regions()

    # create a generator, initialise it and run the simulation
    gen = Generator()
    gen.initialize(lattice)
    gen.run()
    gen.terminate()

    #----------------------------------------------------------