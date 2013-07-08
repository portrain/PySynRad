import os
import sys
import json

from string import Template

class __SettingsSingleton(object):
    d = {}


def Settings():
    return __SettingsSingleton().d


def read(conf_path):
    # read the settings file and store the result into the dictionary
    Settings().clear()
    Settings().update(json.load(open(conf_path, 'r')))

    # store file path of the configuration file
    Settings()['application']['conf_path'] = os.path.abspath(os.path.dirname(conf_path))
