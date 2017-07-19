#!/usr/bin/env python

import logging
import logging.handlers
import argparse
import sys
import time

import i4media.core
import i4media.streaming
import i4media.restapi


LOG_FILENAME = "/tmp/i4media.log"
LOG_LEVEL = logging.DEBUG

parser = argparse.ArgumentParser(description='i4Media-twitter Service Controller')
parser.add_argument(
    '-s',
    '--stream',
    default=False,
    action='store_true',
    help='Starts a Streaming Service & Bridge')
parser.add_argument(
    '-r',
    '--rest',
    default=False,
    action='store_true',
    help='Starts REST Api (Single')

parser.add_argument("-l", "--log", help="file to write log to (default '%s')" % LOG_FILENAME)

# If the log file is specified on the command line then override the default
args = parser.parse_args()

if args.log:
        LOG_FILENAME = args.log

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# STDOUT
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


if __name__ == '__main__':
    p = i4media.core.Process()
    services = []
    if args.stream:
        services.append(i4media.streaming.StreamingService())
        p.add('streaming', services[-1].stream)
        services.append(i4media.streaming.StreamingBridge())
        p.add('bridge', services[-1].start)
    if args.rest:
        services.append(i4media.restapi.RestApiBridge())
        p.add('rest', services[-1].start)
    p.start()
