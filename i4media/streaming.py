import logging
import json

from .core import Bridge, Service
from .config import *


# Bridge Extension for Streaming Service ##
class StreamingBridge(Bridge):
    def apps(self):
        super(StreamingBridge, self).apps()

        @self.app.route("/test")
        def stream_on():
            return self.flask.jsonify('Nothing')


class StreamingService(Service):
    def get_keywords(self):
        return self.get_key_json(STREAM_KEY, CONFIG_KEYWORDS)

    def get_api_key(self):
        return self.get_key_json(STREAM_API, CONFIG_APIKEYS)

    def get_user_ids(self):
        """ret = []
        for uid in self.get_key_json(STREAM_TRACK, CONFIG_TRACKS):
            ret.append(int(uid))
        return ret if len(ret) else None"""
        return self.get_key_json(STREAM_TRACK, CONFIG_TRACKS)

    def stream(self):
        self.connect_twitter_api()
        follow = self.get_user_ids()
        track = self.get_keywords()
        langs = STREAM_LANGS
        if 'all' in langs:
            langs = None
        try:
            logging.info('Starting Streaming Service')
            for status in self.api.GetStreamFilter(
                    track=track,
                    follow=follow,
                    languages=langs
            ):
                self.queue.rpush(STREAM_PUSHTO, json.dumps(status))
                logging.info('Tweet Pushed to Redis')
        except self.TwitterError as e:
            logging.critical('ERROR IN STREAM %s' % e.message)
