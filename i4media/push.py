import logging
import json

import dbext
from .core import Bridge, Service
from .config import *


class PushBridge(Bridge):
    def apps(self):
        super(Bridge, self).apps()

        @self.route('/bridge')
        def bridge():
            return self.flask.Response('bridge')


class PushService(Service):
    def push(self):
        logging.info('Starting Push Service')
        while True:
            try:
                item = self.queue.blpop(API_PUSHTO, 0)[1]
                if not dbext.insert_tweet(json.loads(item)):
                    logging.ERROR('Error Inserting a Tweet')
                    self.queue.rpush('insert_errors', item)
            except:
                continue
