import redis
import logging
import time
import multiprocessing as mp
import flask
from flask_cors import CORS
# from flask_wtf.csrf import CSRFProtect
import twitter
import requests
from requests.auth import HTTPBasicAuth
import json

from .config import *


# Bridge Object ##
class Bridge(object):
    app = None
    services = []
    flask = None
    # csrf = None
    updater_request_status = 0

    def __init__(self):
        # Load Needed Flask Functions for Bridge Extensions
        self.flask = flask
        self.app = flask.Flask(__name__)
        self.app.config['PROPAGATE_EXCEPTIONS'] = True
        self.app.logger.addHandler(handler)
        self.app.logger.addHandler(ch)
        CORS(self.app)
        # CORS(
        #     self.app,
        #     resources={
        #         r"/get/*": {
        #            "origins": "*"}})
        # WTF_CSRF_SECRET_KEY = 'TOKEN'
        # self.csrf = CSRFProtect(self.app)

    def apps(self):
        # @self.csrf.exempt
        @self.app.route("/update/trigger")
        def updater():
            return self.updater()

    def start(self):
        self.apps()
        self.app.run(host=BRIDGE_HOST)

    def updater(self):
        logging.info('Updater Started')
        r = self._updater_request(UPDATER_URL)
        if r:
            logging.debug('Updater lst file received')
            self._updater_lst(r.json())

    def _updater_lst(self, lst):
        errors = []
        for fi, uri in list(lst.items()):
            r = self._updater_request(uri)
            if not r:
                errors.append((
                    self.updater_request_status,
                    fi,
                    uri
                ))
                continue
            if not self._updater_json_write(fi, r.json()):
                errors.append((
                    None,
                    fi,
                    r.json()
                ))
                logging.error(
                    "!!!THE FILE %s MAY BE CORRUPTED OR MISSING!!!" % fi.upper()
                )
                continue
        if len(errors):
            logging.warning('%d errors found.' % len(errors))

    def _updater_request(self, _url):
        r = requests.get(
            "%s://%s:%s/%s" % (
                UPDATER_PROTOCOL,
                UPDATER_HOST,
                UPDATER_PORT,
                _url
            ),
            auth=HTTPBasicAuth(
                UPDATER_USER,
                UPDATER_PASS
            ),
            timeout=60
        )
        if r.status_code == 200:
            return r
        else:
            self.updater_request_status = r.status_code
            return False

    @staticmethod
    def _updater_json_write(_file, _json):
        try:
            with open(
                '%s/config/%s' % (BASE_DIR, _file),
                "w"
            ) as _cfg_file:
                json.dump(_json, _cfg_file)
        except:
            return False
        return True


class Service(object):
    api = None
    api_tokens = None
    queue = None
    TwitterError = None

    def __init__(self):
        # Connect to REDIS
        self.queue = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True)
        # Load Twitter Exceptions Objects
        self.TwitterError = twitter.TwitterError

    def get_json(self, json_path):
        try:
            with open('%s/%s' % (BASE_DIR, json_path), "r") as json_file:
                return json.load(json_file)
        except:
            return False

    def get_key_json(self, key, json_path, default=0):
        json_file = self.get_json(json_path)
        if key in json_file:
            return json_file[key]
        else:
            logging.log(
                logging.WARN,
                'Keyword %s not found in %s. Returning default #%d' % (key, json_path, default))
            return list(json_file.items())[default]

    def connect_twitter_api(self, key=STREAM_API):
        self.api_tokens = self.get_key_json(key, CONFIG_APIKEYS)
        self.api = twitter.Api(
            self.api_tokens['consumer_key'],
            self.api_tokens['consumer_secret'],
            self.api_tokens['access_token'],
            self.api_tokens['access_token_secret'],
            sleep_on_rate_limit=GLOBAL_RATESLEEP)


class Process(object):
    process = []
    loaded = {}

    def __init__(self):
        pass

    def start(self):
        logging.log(logging.INFO, 'Starting Process Sentinel Service')
        for pr in self.process:
            pr.daemon = True
            # Don't use try here. So if errors occurs, the service wont start a useless loop
            pr.start()
        for pr in self.process:
            pr.join()
        self.sentinel()

    def add(self, name, target, args=None, kwargs=None):
        all_args = {
            'target': target,
            'name': name
        }
        if args:
            all_args['args'] = args
        if kwargs:
            all_args['kwargs'] = kwargs
        self.process.append(mp.Process(**all_args))
        self.loaded[name] = {
            'target': target,
            'name': name,
            'args': args,
            'kwargs': kwargs
        }
        logging.log(logging.INFO, 'Loaded %s to process list' % name)

    def sentinel(self, sleep=60):
        while True:
            errors = 0
            # Checking Process Status
            for pr in self.process:
                if not pr.is_alive():
                    errors += 1
                    # Found an error in a process
                    logging.log(logging.ERROR, 'Process %s is dead' % pr.name)
                    # Removing from active list
                    self.process.remove(pr)
                    try:
                        # Try to load the process again
                        self.process.append(self.loaded[pr.name])
                        self.process[-1].start()
                        # The process started success
                        errors -= 1
                    except:
                        # Process Didn't Started
                        logging.critical(
                            'Cant Restart Process %s' % pr.name,
                            self.loaded[pr.name],
                            pr)
            sleep_time = 10 if errors else sleep
            time.sleep(int(sleep_time))