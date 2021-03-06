# General Imports
import os
import datetime
import json
from flask import request
from flask_cors import cross_origin
# i4media Imports
from .core import *
import dbext


# Bridge Extension for RestAPI Service ##
class RestApiBridge(Bridge):
    def apps(self):
        super(RestApiBridge, self).apps()

        """
        @self.csrf.exempt
        @self.app.route("/generate/token")
        def generate_token():
            self.csrf.generate_csrf()
            return self.app.jsonify({'status': 'success'})
        """
        @self.app.route("/get/query/<query>")
        @cross_origin()
        # @self.cache.memoize(timeout=600)
        def get_query(query):
            return self.get_query(query)

        @self.app.route("/get/tsv/<query>")
        @cross_origin()
        # @self.cache.memoize(timeout=600)
        def get_tsv(query):
            return self.get_tsv(query)

        @self.app.route("/get/json/cascade/<query>")
        @cross_origin()
        # @self.cache.memoize(timeout=600)
        def get_json_cascade(query):
            return self.get_json_cascade(query)

        @self.app.route("/get/json/<query>", methods=['POST', 'GET'])
        @cross_origin()
        # @self.cache.memoize(timeout=600)
        def get_json(query):
            return self.get_json(query, True if self.flask.request.method == 'POST' else False)

        @self.app.route("/get/flare/v1/<query>")
        @cross_origin()
        # @self.cache.memoize(timeout=600)
        def get_flare_v1(query):
            return self.get_flare_v1(query)

        # Flare exclusivo para bubble charts
        @self.app.route("/get/flare/bc/<query>", methods=['POST', 'GET'])
        @cross_origin()
        # @self.cache.memoize(timeout=600)
        def get_flare_bc(query):
            return self.get_flare_v2(
                query,
                'id,value,screenName,nombreCandidato',
                ['frente', 'bloque', 'candidato'],
                ['menciones', 'screenName', 'nombreCandidato'])

        @self.app.route("/get/flare/nobase/<query>")
        @cross_origin()
        # @self.cache.memoize(timeout=600)
        def get_flare_nobase(query):
            return self.get_flare_v1(query, base=None)

    @staticmethod
    def query_json(query):
        with open('%s/%s' % (PROJECT_ROOT, CONFIG_QUERIES)) as js:
            qs = json.load(js)
        if query in qs:
            return qs[query]
        else:
            return None

    # Queries Cache Control Methods #
    # This will try to read a cache file for the specified query #
    @staticmethod
    def cache_read(query, ext):
        name = '%s/cache/%s.%s' % (PROJECT_ROOT, query, ext)
        try:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(name))
        except OSError:
            return False
        if mtime > datetime.datetime.now() - datetime.timedelta(hours=3):
            with open(name, 'r') as cache:
                if ext == 'json' or ext == 'query':
                    return json.load(cache)
                else:
                    return cache.read()
        else:
            return False
        # return False

    # This will write the query result to cache file #
    @staticmethod
    def cache_write(query, ext, ret):
        name = '%s/cache/%s.%s' % (PROJECT_ROOT, query, ext)
        try:
            with open(name, "w") as cache:
                if ext == 'tsv' or ext == 'csv':
                    cache.write('%s' % ret.encode('utf-8'))
                if ext == 'json' or ext == 'query':
                    cache.write(json.dumps(ret))
        except IOError:
            return False
        return True
        # pass

    # Return the query from queries.json #
    def get_query(self, query):
        cache = self.cache_read(query, 'query')
        if cache:
            return self.flask.jsonify(cache)
        ret = {}
        q = self.query_json(query)
        if q:
            res = dbext.raw_sql(q)
            c = 0
            for row in res:
                ret[c] = {}
                for k, v in list(row.items()):
                    ret[c][k] = v
                c += 1
        else:
            ret = {'error': True}
        if len(ret) <= 1:
            ret = ret[0]
        self.cache_write(query, 'query', ret)
        return self.flask.jsonify(ret)

    # Get a Tab Separated File for the query
    def get_tsv(self, query):
        ret = self.cache_read(query, 'tsv')
        if ret:
            return self.flask.Response(
                ret,
                mimetype="text/tsv",
                headers={
                    "Content-disposition":
                    "attachment; filename=data.tsv"
                })
        else:
            ret = ''
        q = self.query_json(query)
        if q:
            res = dbext.raw_sql(q)
            # Headers
            if len(res) < 1:
                return 'None'
            for h, v in list(res[0].items()):
                ret += '%s\t' % h
            ret += '\n'
            # Content
            for row in res:
                for k, v in list(row.items()):
                    if type(v) is float:
                        ret += '%s\t' % '{0:g}'.format(float(v))
                    else:
                        ret += '%s\t' % v
                ret += '\n'
        self.cache_write(query, 'tsv', ret)
        return self.flask.Response(
            ret,
            mimetype="text/tsv",
            headers={
                "Content-disposition":
                "attachment; filename=data.tsv"}
        )

    def get_json(self, query, params=False):
        if params is False:
            cache = self.cache_read(query, 'json')
            if cache:
                return self.flask.jsonify(json.dumps(cache))
        ret = []
        q = self.query_json(query)
        if q:
            if params:
                #  Procesar query con parametros
                # self.flask.Request.get_json()
                # data = request.data
                r = request.get_json(force=True)
                q = q.format(**r)
            res = dbext.raw_sql(q)
            for row in res:
                arr = {}
                for k, v in list(row.items()):
                    arr[k] = v
                ret.append(arr)
            if params is False:
                self.cache_write(query, 'json', ret)
        else:
            ret = {'error': True}
        return self.flask.jsonify(json.dumps(ret))

    def get_json_cascade(self, query):
        cache = self.cache_read(query, 'json')
        if cache:
            return self.flask.jsonify(json.dumps(cache))
        ret = []
        q = self.query_json(query)
        if q:
            res = dbext.raw_sql(q)
            c = 'children'
            for row in res:
                for k, v in list(row.items()):
                    if k == 'date':
                        if len(ret) == 0 or ret[-1]['date'] != v:
                            ret.append({
                                "date": v,
                                "name": "Frentes",
                                "children": []
                            })
                            continue
                        else:
                            continue
                    elif k == 'frente':
                        if len(ret[-1][c]) == 0 or ret[-1][c][-1]['name'] != v:
                            ret[-1][c].append({
                                "name": v,
                                "children": []
                            })
                            continue
                        else:
                            continue
                    elif k == 'candidato':
                        if len(ret[-1][c][-1][c]) == 0 or ret[-1][c][-1][c][-1]['name'] != v:
                            ret[-1][c][-1][c].append({
                                "name": v,
                                "size": ""
                            })
                            continue
                        else:
                            continue
                    elif k == 'q_mentions':
                        ret[-1][c][-1][c][-1]['size'] = v
                        break

        else:
            ret = {'error': True}
        self.cache_write(query, 'json', ret)
        return self.flask.jsonify(json.dumps(ret))

    def get_flare_v2(self, query, headers=None, params=[], values=[]):
        q = self.query_json(query)
        if len(params) < 1 or len(values) < 1:
            return 'Missing Params or Values'
        if q:
            # data = request.data
            r = request.get_json(force=True)
            q = q.format(**r)
            res = dbext.raw_sql(q)
            if len(res) < 1:
                return 'None'
                # FLARE START #
            ret = '%s\n' % headers if headers else ''
            for row in res:
                count = 0
                for k, v in list(row.items()):
                    if k in params:
                        ret += "%s%s" % (
                            '.' if count > 0 else '',
                            v.replace(' ', '') if type(v) == str or type(v) == unicode else v)
                        count += 1
                    elif k in values:
                        ret += "%s%s" % (
                            ',',
                            v.replace(' ', '') if type(v) == str or type(v) == unicode else v)
                ret += '\n'
            return self.flask.Response(
                ret,
                mimetype="text/csv",
                headers={
                    "Content-disposition":
                        "attachment; filename=flare.csv"})

    def get_flare_v1(self, query, headers='id,value', base='flare'):
        cache = self.cache_read(query, 'flare')
        if cache:
            return self.flask.Response\
                (cache,
                 mimetype="text/csv",
                 headers={
                     "Content-disposition":
                     "attachment; filename=flare.csv"})
        q = self.query_json(query)
        if q:
            res = dbext.raw_sql(q)
            if len(res) < 1:
                return 'None'
            # FLARE START #
            ret = '%s\n' % headers if headers else ''
            ret += '%s,\n' % base if base else ''
            # for k, v in [row.items() for row in res]:
            for row in res:
                group, subgroup, name, value = ('' for i in range(4))
                for k, v in list(row.items()):
                    if k == 'group':
                        group = v.replace(' ', '') if v else 'NG'
                    elif k == 'subgroup' and v and v != '-':
                        subgroup = v.replace(' ', '') if v else 'NSG'
                    elif k == 'value':
                        value = '%s' % str(v)
                    elif k == 'name':
                        name = v
                if not value and not name:
                    continue
                if name and not value:
                    value = '0'
                if base and subgroup and group:
                    ret += '%s.%s.%s.%s,%s\n' % (base, group, subgroup, name, value)
                elif base and group:
                    ret += '%s.%s.%s,%s\n' % (base, group, name, value)
                elif subgroup and group:
                    ret += '%s.%s.%s,%s\n' % (group, subgroup, name, value)
                elif group:
                    ret += '%s.%s,%s\n' % (group, name, value)
        else:
            ret = 'Query not found'
        self.cache_write(query, 'csv', ret)
        return self.flask.Response(
            ret,
            mimetype="text/csv",
            headers={
                "Content-disposition":
                "attachment; filename=flare.csv"})
