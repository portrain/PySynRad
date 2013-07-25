import os
import json
from string import Template

class __SettingsSingleton(object):
    d = {}


def Settings():
    return __SettingsSingleton().d

def read(conf_path, template_string):
    """
    Read the settings file, replace the template strings and store
    the result into the dictionary
    """
    Settings().clear()
    if template_string != None:
        s_temp = Template(open(conf_path, 'r').read())
        s_json = s_temp.safe_substitute(json.loads(template_string))
        Settings().update(json.loads(s_json))
    else:
        Settings().update(json.load(open(conf_path, 'r')))

    # store file path of the configuration file
    Settings()['application']['conf_path'] = os.path.abspath(os.path.dirname(conf_path))
