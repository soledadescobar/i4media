#!/usr/bin/env python

import logging
import logging.handlers
import argparse
import sys
import time

import i4media.core
import i4media.streaming


LOG_FILENAME = "/tmp/i4media-twitter.log"
LOG_LEVEL = logging.DEBUG

parser = argparse.ArgumentParser(description='i4Media-twitter Service Controller')
parser.add_argument(
    '-s',
    '--stream',
    default=False,
    action='store_true',
    help='Starts a Streaming Service')

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


class MyLogger(object):
        def __init__(self, logger, level):
                """Needs a logger and a logger level."""
                self.logger = logger
                self.level = level

        def write(self, message):
                # Only log if there is a message (not just a new line)
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())


sys.stdout = MyLogger(logger, logging.INFO)
sys.stderr = MyLogger(logger, logging.ERROR)


if __name__ == '__main__':
    p = i4media.core.Process()
    services = []
    if args.stream:
        p.add('streaming', i4media.streaming.StreamingService().stream())
        p.add('bridge', i4media.streaming.StreamingBridge().start())
    p.start()
