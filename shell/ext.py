import time
import twitter
import json
import redis


class ShellApi(object):
    apikeys = []
    keywords = []
    target = ''
    params = {}
    active = {}
    api = None
    queue = None

    def __init__(self, target_kw='keywords'):
        self.params = {
            'term': '',
            'raw_query': '',
            'since': '',
            'until': '',
            'since_id': '',
            'max_id': ''
        }
        self.redis_on('10.128.0.11')
        self.getapikeys()
        self.target = target_kw
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
        print("Reading APIKeys from JSON File\n")
        with open(r'apikeys.json', 'r') as fl:
            ret = json.load(fl)
        print("Loading APIKeys into ShellApi\n")
        self.apikeys = ret.get('apikeys', False)
        if not self.apikeys:
            raise RuntimeError("Failed to load Api Keys\n")

    # This will load the keywords file
    def getkeywords(self):
        print("Loading Keywords from JSON File\n")
        with open('keywords.json', "r") as fl:
            ret = json.load(fl)
        print("Loading %s Keywords into ShellApi\n" % self.target)
        self.keywords = ret.get(self.target, False)
        if not self.keywords:
            raise RuntimeError("Failed to load keywords\n")

    # This will return the next api key data (the first if none is loaded)
    def getapi(self, _id=False):
        if _id:
            print("Returning Specified ApiKey Index '%d'\n" % _id)
            return self.apikeys[_id]
        n = self.active.get('id', 0) + 1 if self.active else 0
        if n > 0:
            if len(self.apikeys) <= n:
                print("APIKeys Exhausted. Starting from 0 in 15 minutes...\n")
                time.sleep(900)
                n = 0
        print("Returning next ApiKey[Index=%d]\n" % n)
        return {'id': n, 'api': self.apikeys[n]}

    # API Connect with the next apikeys
    def getactive(self, _id=False):
        print("Looking for API Keys...\n")
        self.active = self.getapi(_id)
        print("Connecting to Twitter API\n")
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
            "Trying to search keyword: %s\n" % args.get('term', 'no terms')
        )
        try:
            res = self.api.GetSearch(**args)
        except:
            print("Moving on to next ApiKey\n")
            self.getactive()
            return self.search(**args)
        if not len(res):
            return False
        return res

    def timeline(self, **args):
        for k, v in list(args.items()):
            if v == '':
                args[k] = None
        print(
            "Trying to get timeline \n%s" % args
        )
        try:
            res = self.api.GetUserTimeline(**args)
        except:
            print("Moving on to next ApiKey\n")
            self.getactive()
            return self.search(**args)
        if not len(res):
            return False
        return res

    def searchkeyword(
            self,
            keyword,
            method='',
            max_id=None,
            until=None,
            actual=0,
            limit=10):
        terms = getattr(self, 'params_%s' % method, None)().copy()
        if not terms:
            raise RuntimeError("Parameters for method %s not found" % method)
        if 'term' in terms:
            print("Updating Term")
            terms.update(term=keyword)
        if 'screen_name' in terms:
            print("Updating Screen Name")
            terms.update(screen_name=keyword)
        if max_id and 'max_id' in terms:
            print("Updating Max ID")
            terms.update(max_id=max_id)
        if until and 'until' in terms:
            print("Updating Until Date")
            terms.update(until=until)
        print(terms)
        if method == 'search':
            search = self.search(**terms)
        elif method == 'timeline':
            search = self.timeline(**terms)
        else:
            raise NameError("Method %s Not Found" % method)
        if not search or len(search) <= 1:
            print("Search returned 0 results\n")
            return False  # Returning false when there is no more results
        ids = []
        for r in search:
            status = r.AsDict()
            print(
                "Pushing Tweet ID: %s to REDIS. Found with keyword: %s\n" %
                (status.get('id'), keyword)
            )
            self.queue.rpush('stream', json.dumps(status))
            ids.append(status.get('id'))
        ids = sorted(ids, key=int)
        actual += 1
        if actual >= limit:
            return False
        return self.searchkeyword(keyword, method=method, max_id=ids[0], until=until, actual=actual, limit=limit)

    def searchkeywords(self, until=None, method='search', limit=10):
        print("Searching all the keywords with method %s\n" % method)
        for k in self.keywords:
            print("Starting for keyword: %s\n" % k)
            if not self.searchkeyword(k, method=method, until=until, limit=limit):
                print("No more results for %s\n" % k)
                continue
        print("Job seems to be finished\n")

    def params_search(self):
        return {
            'term': '',
            'raw_query': '',
            'since': '',
            'until': '',
            'since_id': '',
            'max_id': ''
        }

    def params_timeline(self):
        return {
            'user_id': '',
            'screen_name': '',
            'since_id': '',
            'max_id': '',
            'include_rts': '',
            'exclude_replies': '',
            'count': 200,
            'trim_user': False
        }