import json
import os
import sys
import logging.handlers


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
                if type(v) == str or type(v) == unicode \
                else '%s' % v
            exec (
                '%s_%s = %s' %
                (str(i).upper(), str(k).upper(), value)
            )
    elif type(CONFIG[i]) == list:
        exec ('%s = %s' % (str(i).upper(), CONFIG[i]))
    elif type(CONFIG[i]) == str or type(CONFIG[i]) == unicode:
        exec('%s = "%s"' % (str(i).upper(), CONFIG[i]))

# # Try to get Log Level from config file variable
try:
    logging_level = ''
    exec ("logging_level = logging.%s" % LOG_LEVEL.upper())
except:
    # If that level doesn't exist in logging class, use default value
    logging_level = logging.DEBUG
#
# LOG_FILE = '/tmp/i4media.log'
# logging.basicConfig(filename=LOG_FILE, level=logging_level, stream=sys.stdout)

logger = logging.getLogger(__name__)
logger.setLevel(logging_level)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# STDOUT
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

del(i, k, v, value, config_file)

logger.info('i4media Configuration Loaded')
