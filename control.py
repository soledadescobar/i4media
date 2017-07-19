#!/usr/bin/env python

import argparse
from i4media.logger import *

import i4media.core
import i4media.streaming
import i4media.restapi


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
args = parser.parse_args()

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
