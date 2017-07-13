import time
import twitter
import json
import redis


class ShellApi(object):
    apikeys = []
    keywords = []
    params = {}
    active = {}
    api = None
    queue = None

    def __init__(self):
        self.params = {
            'term': '',
            'raw_query': '',
            'since': '',
            'until': '',
            'since_id': '',
            'max_id': ''
        }
        self.redis_on()
        self.getapikeys()
        self.getkeywords()
        self.getactive()
        print("""
            -- ShellApi Object Created --
        """)

    # Connect redis
    def redis_on(self, host='localhost', port=6379):
        self.queue = redis.Redis(
            host=host, port=port,
            decode_responses=True)

    # This will load the api keys file
    def getapikeys(self):
        print("Reading APIKeys from JSON File")
        with open(r'apikeys.json', 'r') as fl:
            ret = json.load(fl)
        print("Loading APIKeys into ShellApi")
        self.apikeys = ret.get('apikeys', False)
        if not self.apikeys:
            raise RuntimeError("Failed to load Api Keys")

    # This will load the keywords file
    def getkeywords(self):
        print("Loading Keywords from JSON File")
        with open('keywords.json', "r") as fl:
            ret = json.load(fl)
        print("Loading Keywords into ShellApi")
        self.keywords = ret.get('keywords', False)
        if not self.keywords:
            raise RuntimeError("Failed to load keywords")

    # This will return the next api key data (the first if none is loaded)
    def getapi(self, _id=False):
        if _id:
            print("Returning Specified ApiKey Index '%d'" % _id)
            return self.apikeys[_id]
        n = self.active.get('id', 0) + 1 if self.active else 0
        if n > 0:
            if len(self.apikeys) <= n:
                print("APIKeys Exhausted. Starting from 0 in 1 minute...")
                time.sleep(60)
                n = 0
        print("Returning next ApiKey[Index=%d]" % n)
        return {'id': n, 'api': self.apikeys[n]}

    # API Connect with the next apikeys
    def getactive(self, _id=False):
        print("Looking for API Keys...")
        self.active = self.getapi(_id)
        print("Connecting to Twitter API")
        self.api = twitter.Api(
            self.active['api']['consumer_key'],
            self.active['api']['consumer_secret'],
            self.active['api']['access_token'],
            self.active['api']['access_token_secret'],
            sleep_on_rate_limit=False)

    def search(self, **args):
        for k, v in list(args.items()):
            if v == '':
                args[k] = None
        print(
            "Trying to search %s" % args
        )
        try:
            res = self.api.GetSearch(**args)
        except:
            print("EXCEPTION FOUND")
            print("Moving on to next ApiKey")
            self.getactive()
            return self.apicall(**args)
        if not len(res):
            return False
        return res

    def searchkeyword(self, keyword, max_id=None):
        terms = self.params.copy()
        terms.update(term=keyword)
        if max_id:
            terms.update(max_id=max_id)
        search = self.search(**terms)
        if not search:
            print("Search returned 0 results")
            return False  # Returning false when there is no more results
        ids = []
        for r in search:
            status = r.AsDict()
            print(
                "Pushing Tweet ID: %s to REDIS. Found with keyword: %s" %
                (status.get('id'), keyword)
            )
            self.queue.rpush('stream', json.dumps(status))
            ids.append(status.get('id'))
        ids = sorted(ids, key=int)
        return self.searchkeyword(keyword, max_id=ids[0])

    def searchkeywords(self):
        print("Searching all the keywords")
        for k in self.keywords:
            print("Starting for keyword: %s" % k)
            if not self.searchkeyword(k):
                print("No more results for %s" % k)
                continue
        print("Job seems to be finished")
