import json
import os
import sys

from .logger import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'i4media'))

with open('%s/config/config.json' % BASE_DIR, "r") as config_file:
    CONFIG = json.load(config_file)


for i in CONFIG:
    if type(CONFIG[i]) == dict:
        for k, v in list(CONFIG[i].items()):
            value = \
                '"%s"' % v \
                if type(v) == str \
                else '%s' % v
            exec(
                '%s_%s = %s' %
                (str(i).upper(), str(k).upper(), value)
            )
    elif type(CONFIG[i]) == list:
        exec('%s = %s' % (str(i).upper(), CONFIG[i]))
    elif type(CONFIG[i]) == str:
        exec('%s = "%s"' % (str(i).upper(), CONFIG[i]))

del(i, k, v, value, config_file)


