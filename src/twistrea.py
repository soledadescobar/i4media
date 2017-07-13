import sys
import psutil
import datetime
import os.path
from sqlalchemy import *
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql import func
import sqlalchemy.ext
from sqlalchemy.sql import text
#from sqlalchemy.engine import reflection
from termcolor import colored
import time
import logging
from types import *
import re
import multiprocessing as mp
import json
import redis
import configparser
import twitter
from pid import PidFile
from flask import Flask, jsonify, request, Response
import libtmux


# Envia los errores a REDIS
def except_redis(func):
    def wrapper(self, *arg, **kw):
        try:
            func(self, *arg, **kw)
        except Exception as e:
            self.BridgeLog(e)
            raise
    return wrapper


class Twistreapy(object):
    keywords = []  # Lista de Keywords
    track = False  # Controla los keywords en stream
    langs = []  # Lista de todos los lenguajes en la lista de keywords
    user_ids = []  # IDs de Usuario
    follow = False  # Controla los User_ids en stream
    process = []  # Lista de Procesos
    queue = None  # REDIS Queue
    pgs = None  # PostgreSQL Conn
    api = None  # Twitter API
    apicfg = None  # API Config
    rates = None  # Rates Confg
    limits = None  # Per-Request Limits
    pidcfg = []  # Pid File Config
    orm = None  # Database ORM
    dbeng = None  # Database Engine
    session = None  # Database Session
    models = {}  # Modelos de Datos Cargados
    types = {}  # Relacion de Tipos de Datos
    entities = []
    cp = None  # ConfigParser Object

    def __init__(self, ini_path='config.ini'):
        self.ini = ini_path
        ### Leo el archivo de configuraciones
        self.cp = configparser.ConfigParser()
        self.cp.read(self.ini)
        cp = self.cp
        ### Logging
        logging.basicConfig(filename=cp['LOG']['file'], level=logging.DEBUG)
        ### Rates & Limits
        self.rates = cp['RATES']
        self.limits = cp['LIMITS']
        ### Configuraciones de Parametros de la API
        apicfg = cp['API']
        self.apicfg = apicfg
        self.api = twitter.Api(apicfg['consumer_key'],
            apicfg['consumer_secret'], apicfg['access_token'],
            apicfg['access_token_secret'], sleep_on_rate_limit=True)
        ### Configuracion PID (Proccess ID File Lock)
        self.pidcfg = cp['PID']
        ### Configuracion Redis
        redcfg = cp['REDIS']
        ### Conexiones a Redis Queue
        self.queue = redis.Redis(host=redcfg['host'], port=redcfg['port'],
            decode_responses=True)
        ### Configuracion DB
        self.pcfg = cp['DATABASE']
        ### Conexion a DB
        if self.pcfg.getboolean('use'):
            self.connect_database()
        self.types = {'INTEGER': 'int', 'VARCHAR': 'str', 'BIGINT': 'int',
             'TEXT': 'str', 'TINYINT': 'int'}
        ### Cargo las Keywords, Lang y User IDS
        with open('keywords.json') as kwFile:
            kws = json.load(kwFile)
        self.keywords = kws.get('keywords', apicfg['keywords'].split(','))
        self.track = apicfg.getboolean('stream_enable_keywords')
        self.langs = apicfg['langs'].split(',')
        if kws.get('keywords.json', False):
            for ud in kws.get('keywords'):
                if ud.startswith('@'):
                    self.user_ids.append(ud)
        else:
            self.user_ids = apicfg['user_ids'].split(',')
        self.follow = apicfg.getboolean('stream_enable_user_ids')
        ### Cargo entities
        self.entities = self.apicfg['entities'].split(',')

### Procesos Core ###
# Inicio de los procesos, lockeando el PID en el archivo configurado
    def Start(self):
        with PidFile(pidname=self.pidcfg['name'], piddir=self.pidcfg['dir']):
            self.ProcSentinel()

# Inicio de los procesos
# OJO CON TOCAR ESTO
    def ProcSentinel(self, sleep=60):
        sleeptime = sleep
        load = {}
        if self.apicfg.getboolean('ffs_sentinel') is True:
            load['followers_sentinel'] = "self.process.append(mp.Process(name=\
'followers_sentinel', target=self.followersSentinel, args=()))"
        if self.apicfg.getboolean('users_lookup') is True:
            load['users_lookup'] = "self.process.append(mp.Process(name='users_\
lookup', target=self.UsersLoop, args=('rest-users', )))"
        if self.apicfg.getboolean('poploop') is True:
            load['poploop'] = "self.process.append(mp.Process(name='poploop',\
target=self.poploop, args=('stream', )))"
        if self.apicfg.getboolean('stream') is True:
            load['stream'] = "self.process.append(mp.Process(name='stream', tar\
get=self.Stream, args=('stream', )))"
        for l in list(load.values()):
            exec(l)
        for pr in self.process:
            pr.daemon = True
            pr.start()
        while True:
            errors = 0
            self.pc('Checking Process Status', 'cyan')
            for pr in self.process:
                if not pr.is_alive():
                    errors += 1
                    self.pc('Error in process: ' + str(pr.name), 'red')
                    self.process.remove(pr)
                    self.pc('Executing Restart Code: ' +
                        str(load.get(pr.name)), 'blue')
                    try:
                        exec(load.get(pr.name))
                        self.process[-1].start()
                        self.pc('[Process started Succesfull', 'blue')
                        errors -= 1
                    except:
                        error = "Couldn't Start Appended Process with name: \
%s.]\n[Process name should be: %s. " % \
(str(self.process[-1].name), str(pr.name))
                        self.pc(error, 'red')
            if errors == 0:
                self.pc('All Process Running', 'green')
                sleeptime = sleep
            else:
                self.pc('Errors in process found. Retry in 10 secs', 'red')
                sleeptime = 10
            time.sleep(int(sleeptime))

# Proceso de Stream
    @except_redis
    def Stream(self, key):
        track = self.keywords
        follow = self.user_ids
        langs = self.langs
        self.pc('Starting Twitter Streaming API in List: [' + key +
            '] for Keywords: ', 'blue')
        ### Agrego cada keyword a la lista Follow si es un usuario
        ### O a la lista track para buscar expresiones
        if track:
            for kw in track:
                if kw.startswith('@'):
                    self.pc('\tMentions of: [' + kw + ']', 'cyan', False)
                elif kw.startswith('#'):
                    self.pc('\tHashtag: [' + kw + ']', 'magenta', False)
                else:
                    self.pc('\t Expresion: [' + kw + ']', 'magenta', False)
        else:
            track = None
        if follow:
            for fw in follow:
                self.pc('\tUser ID: [' + fw + ']', 'cyan', False)
        else:
            follow = None
        self.pc('\tSelected Languages:', 'blue', False)
        if 'all' in langs:
            langs = None
            self.pc('\t[all]', 'magenta', False)
        else:
            for lang in langs:
                self.pc('\t[' + lang + ']', 'cyan', False)
        for status in self.api.GetStreamFilter(track=track, follow=follow,
            languages=langs):
            self.queue.rpush(key, json.dumps(status))
            self.pc('New Tweet Pushed to list: ' + key, 'green')

# Bucle Inifinito de Popblock
    @except_redis
    def poploop(self, keys):
        self.pc('Starting PopLoop Service for List: ' + keys + '', 'blue')
        while True:
            item = self.queue.blpop(keys, 0)[1]
            self.pc('Pushing Tweet to SQL', 'green')
            '''try:
                self.insert_tweet(json.loads(item))
            except:
                logging.error(sys.exc_info())
                traceback.print_exc()
                self.pc('SQL Insertion Error, Moving Tweet to Redis', 'red')
                self.queue.rpush('insert_errors', item)
                '''
            if not self.insert_tweet(json.loads(item)):
                self.pc('SQL Insertion Error, Moving Tweet to Redis', 'red')
                self.queue.rpush('insert_errors', item)

### Funciones Rest ###
    def UsersLoop(self, key):
        self.pc('Peticiones para Datos de Usuarios en lista "%s"' % key, 'blue')
        while True:
            item = self.queue.blpop(key, 0)[1]
            ## El item tendria que ser una lista con 100 user ids
            self.usersLookup(json.loads(item))

# Bucle Infinito para levantar Queues Rest
    def RestQueue(self, key, target, count, sleep=180, repeat=0):
        self.pc('Starting REST for Queue ' + key, 'blue')
        # setattr(self, key, [])
        step = 0
        while step < repeat or step == 0:
            self.RestLoop(key, target, count, sleep)
            step += 1

# Levanta Queue para la KEY especifica y llama a la funcion target
    def RestDoList(self, key, target):
        # getattr(self, key).append(self.queue.blpop(key, 0))
        # item = self.queue.blpop(key, 0)
        # getattr(self, target)(item[1])
        count = self.queue.llen(key)
        items = []
        for x in range(0, count):
            items.append(self.queue.lpop(key))
        if(len(items) < count):
            self.pc('Items to process are less than list count for list ' +
            key, 'red')
        self.pc('Processing REST Queue key: ' + key + ' with target: ' + target,
            'blue')
        getattr(self, target)(items)

# Agrupa info para pedidos REST
    def RestLoop(self, key, target, count, sleep):
        found = self.queue.llen(key)
        if(found >= count):
            self.RestDoList(key, target)
        else:
            self.pc('REST Queue ' + key + ' found ' + str(found) + ' items. ' +
            'Waiting for : ' + str(count), 'cyan')
            time.sleep(sleep)

# Followers Sentinel
    def followersSentinel(self):
        ## Sentinela para los cambios de followers
        for i in self.user_ids:
            self.pc('REST F/F\'s IDs for ID:%s' % str(i), 'blue')
            self.followersIDsPaged(i)
            self.friendsIDsPaged(i)
        for i in self.user_ids:
            fl = []
            key = 'staging-followers-%s' % str(i)
            count = self.queue.llen(key)
            for x in range(0, count):
                item = self.queue.lpop(key)
                for uid in json.loads(item):
                    fl.append(int(uid))
            fr = []
            key = 'staging-friends-%s' % str(i)
            count = self.queue.llen(key)
            for x in range(0, count):
                item = self.queue.lpop(key)
                for uid in json.loads(item):
                    fr.append(int(uid))
            self.insert_ffs(i, fl, fr)
            if len(fl) > 0:
                self.usersPutQueue(fl)
            if len(fr) > 0:
                self.usersPutQueue(fr)

#Followers Single User
    def followersSingle(self, user_id):
        self.followersIDsPaged(user_id)
        self.friendsIDsPaged(user_id)
        fl = []
        key = 'staging-followers-%s' % str(user_id)
        count = self.queue.llen(key)
        for x in range(0, count):
            item = self.queue.lpop(key)
            for uid in json.loads(item):
                fl.append(int(uid))
        fr = []
        key = 'staging-friends-%s' % str(user_id)
        count = self.queue.llen(key)
        for x in range(0, count):
            item = self.queue.lpop(key)
            for uid in json.loads(item):
                fr.append(int(uid))
        self.insert_ffs(user_id, fl, fr)
        if len(fl) > 0:
            self.usersPutQueue(fl)
        if len(fr) > 0:
            self.usersPutQueue(fr)
        return

#
    def usersPutQueue(self, ids):
        self.session_start()
        q = []
        for i in ids:
            if len(q) >= int(self.limits['users_lookup']):
                self.queue.rpush('rest-users', q)
                q = []
            if self.session.query(
                self.orm.classes.users.id
            ).filter(
                self.orm.classes.users.id_user == i
            ).first() is None:
                q.append(i)
        if len(q):
            self.queue.rpush('rest-users', q)

# Convierte screen_name a user_id. Si se pasan screen_names, devuelve una lista
# con tuplas. Si no se pasan screen names, lee los screen names en las keywords
# y guarda los ids en cfg
    def convertScreenNames(self, screen_names=False):
        if screen_names:
            save = False
        else:
            screen_names = self.keywords
            save = True
        sn = []
        for nm in screen_names:
            if nm.startswith('@'):
                sn.append(nm[1:])
        ret = self.api.UsersLookup(
            screen_name=sn,
            include_entities=False)
        if save:
            ids = ''
            full = ''
            regex = r"ID=(\d+), ScreenName=(\w+)"
            for r in re.findall(regex, str(ret)):
                ids += str(r[0]) + ','
                full += '(' + str(r[0]) + ", '@" + str(r[1]) + "'), "
            ids = ids.rstrip(',')
            self.writeConfig('API', [('user_ids', ids), ('belongs', full)])
            print(('Wrote :' + full))
        else:
            print((str(ret)))
            return ret

    def convertNamesIds(self, screen_names=False, user_ids=False):
        rt = {}
        sn = []
        for nm in screen_names:
            if nm.startswith('@'):
                sn.append(nm[1:])
        ret = self.api.UsersLookup(screen_name=sn, user_id=user_ids,
            include_entities=False)
        regex = r"ID=(\d+), ScreenName=(\w+)"
        for r in re.findall(regex, str(ret)):
            rt[r[0]] = r[1][:1]
        return rt

# Busca Usuarios por User_ID y envia a REDIS
    def usersLookup(self, user_ids):
        for res in self.api.UsersLookup(user_id=user_ids,
            include_entities=False):
            #self.queue.rpush('users', json.dumps(res))
            self.insert_userdata(res.AsDict())

# Busca Usuarios por Screen_Name y envia a REDIS
    def usersLookupName(self, screen_names=None):
        for res in self.api.UsersLookup(screen_name=screen_names,
        include_entities=False):
            self.queue.rpush('users', json.dumps(res))

# Busca los ID de los Followers del usuario especificado
    def followersIds(self, user_id):
        # Devuelve un cursor, id de pagina y lista de IDS
        for res in self.api.GetFollowerIDsPaged(user_id=user_id):
            if type(res) is ListType:
                push = dict(userid=user_id, followers=res)
                self.queue.rpush('staging-followers', json.dumps(push))

#
    def followersPaged(self, user_id, page=-1):
        p = n = c = 0
        for res in self.api.GetFollowersPaged(user_id=user_id, cursor=page):
            if c == 0:
                n = res
            elif c == 1:
                p = res
            else:
                self.pc('Pushing Followers to Redis', 'blue')
                for user in res:
                    self.queue.rpush(
                        'staging-followers-%s' % str(user_id),
                        user.AsJsonString())
            c += 1
        if n > p and n != 0:
            self.followersPaged(user_id, n)

#
    def followersIDsPaged(self, user_id, page=-1):
        p = n = c = 0
        for res in self.api.GetFollowerIDsPaged(user_id=user_id, cursor=page):
            if c == 0:
                n = res
            elif c == 1:
                p = res
            else:
                self.pc('Pushing Followers to Redis', 'blue')
                self.queue.rpush(
                    'staging-followers-%s' % str(user_id),
                    res)
            c += 1
        if n > p and n != 0:
            self.followersIDsPaged(user_id, n)

#
    def friendsIDsPaged(self, user_id, page=-1):
        p = n = c = 0
        for res in self.api.GetFriendIDsPaged(user_id=user_id, cursor=page):
            if c == 0:
                n = res
            elif c == 1:
                p = res
            else:
                self.pc('Pushing Friends to Redis', 'blue')
                self.queue.rpush(
                    'staging-friends-%s' % str(user_id),
                    res)
            c += 1
        if n > p and n != 0:
            self.friendsIDsPaged(user_id, n)

### Metodos Base de Datos ###
    def session_start(self):
        self.session = Session(self.dbeng)

    @except_redis
    def session_add(self, add):
        self.session.add(add)

    def session_commit(self):
        try:
            self.session.commit()
        except sqlalchemy.exc.DBAPIError as e:
            self.pc(e.args[0], 'red')
            return False
        return True

    @except_redis
    def connect_database(self):
        self.orm = automap_base()
        self.dbeng = create_engine('%s://%s:%s@%s/%s' % (self.pcfg['engine'],
self.pcfg['user'], self.pcfg['pass'], self.pcfg['host'], self.pcfg['name']))
        #    , pool_size=30, max_overflow=100, pool_timeout=60)
        self.orm.prepare(self.dbeng, reflect=True)
        self.conn = self.dbeng.connect()

    def raw_sql(self, sql):
        s = text(sql)
        return self.conn.execute(s).fetchall()

### Inserta un Tweet
    def insert_tweet(self, tweet, id_user=None):
        self.pc('Insertando Tweet ID: %s' % str(tweet['id']), 'blue')
        # Muevo el id del tweet al campo id_tweet
        tweet['id_tweet'] = tweet.pop('id')
        # Cargo el modelo tweets
        self.models['tweets'] = self.orm.classes.tweets
        # Carga de Entities
        if 'entities' in tweet:
            self.pc('El tweet tiene entities', 'cyan')
            for ent in self.entities:
                if ent in tweet['entities']:
                    self.insert_entity(('tweet', tweet['id_tweet'], ent),
                                    tweet['entities'][ent])
        # Carga alternativa de entities
        for ent in self.entities:
            if ent in tweet:
                self.pc('Entidad %s encontrada' % ent, 'cyan')
                self.insert_entity(
                    ('tweet', tweet['id_tweet'], ent),
                    tweet[ent]
                )
        if tweet.get('user', False):
            # Cargo los datos del usuario
            tweet['id_user'] = tweet['user']['id']
            self.insert_userdata(tweet['user'])
        elif id_user:
            tweet['id_user'] = id_user
        else:
            return False
        # Por cada campo de la tabla tweets, busco el mismo campo en el objeto
        # tweet recibido y lo cargo al al dict para insertar
        add = {}
        for key in list(self.models['tweets'].__dict__.keys()):
            if key in tweet:
                add[key] = tweet.get(key)
        self.session_start()
        self.session_add(self.models['tweets'](**add))
        self.session_commit()
        return True

#### Insert userdata
    def insert_userdata(self, user):
        '''if self.session.query(self.orm.classes.users).filter_by(
                id_user=user.get('id')).count():
            self.pc(
                'User ID %s ya existe. No se puede insertar' % user.get('id'),
                'red')
            return False'''
        self.session_start()
        self.pc('Insertando User ID: %s' % str(user['id']), 'blue')
        user['id_user'] = user.pop('id')
        add = {}
        if 'status' in user:
            self.insert_tweet(user['status'], user['id_user'])
        self.models['users'] = self.orm.classes.users
        for key in list(self.models['users'].__dict__.keys()):
            if key in user:
                add[key] = user.get(key)
        self.session_add(self.models['users'](**add))
        return self.session_commit()

## Inserta lista de objetos twitter user
    def insert_user_list(self, userlist):
        for user in userlist:
            self.insert_userdata(user)

#
    def insert_ffs(self, user_id, followers, friends):
        self.session_start()
        add = {}
        self.pc('Insertando F/F\'s para ID: %s' % str(user_id), 'blue')
        self.models['friendfollower'] = self.orm.classes.friendfollower
        add['user_id'] = user_id
        add['followers'] = followers
        add['followers_count'] = len(followers)
        add['friends'] = friends
        add['friends_count'] = len(friends)
        add['created'] = func.now()
        self.session_add(self.models['friendfollower'](**add))
        self.session_commit()

#
    def insert_friends(self, user_id, friends):
        self.session_start()
        add = {}
        self.pc('Insertando Friends para ID: %s' % str(user_id), 'blue')
        self.models['friends'] = self.orm.classes.friends
        add['user_id'] = user_id
        add['friends'] = friends
        add['total'] = len(friends)
        self.session_add(self.models['friends'](**add))
        self.session_commit()

### Inserta un objeto relacionado a un id_tweet
# obj = ( objeto_padre, id_objeto_padre, nombre_entiedad)
# cont = contenido de la entidad
    def insert_entity(self, obj, cont):
        if not cont:
            return False
        for c in cont:
            if not hasattr(c, 'get'):
                return False
            exec("add = {'id_%s': %s}" % (obj[0], obj[1]))
            if 'id' in c:
                exec("c['id_%s'] = c.pop('id')" % obj[2])
            exec("self.models['%s'] = self.orm.classes.%s" % (obj[2], obj[2]))
            for key in list(self.models[obj[2]].__dict__.keys()):
                if key in c:
                    add[key] = c.get(key)
            if len(add) > 0:
                self.session_start()
                self.session_add(self.models[obj[2]](**add))
                return self.session_commit()
        return False

### Helpers Base de Datos
    def compare_types(self, cast, var):
        ret = var
        regex = r"\'\,\ ([A-Z]+)\("
        r = re.search(regex, str(cast))
        if r:
            if type(var) is StringType:
                if r.group(1) == 'VARCHAR':
                    pass
                else:
                    exec('ret = %s(%s)', (self.types.get(r.group(1)), var))
            elif type(var) is IntType:
                if r.group(1) == 'INTEGER' or r.group(1) == 'BIGINT' or \
                r.group(1) == 'TINYINT':
                    pass
                else:
                    exec('ret = %s(%s)' % (self.types.get(r.group(1)), var))
            elif type(var) is NoneType:
                exec('ret = %s()' % self.types.get(r.group(1)))
            elif type(var) is BooleanType:
                exec('ret = %s(%s)' % (self.types.get(r.group(1)), var))
            elif type(var) is DictType:
                # Si es un Dict es una relacion a otra tabla
                exec('ret = %s(%s)' % (self.types.get(r.group(1)), var))
        else:
            self.pc('compare_types(): Regex comparison failed', 'red')
        return ret

### Metodos para ManageCenter Bridge
# Loguea en redis
    def BridgeLog(self, value):
        self.queue.rpush('ERRORS-twistreapy', value)
        self.pc(value, 'red')

# REST POST
    def BridgePost(self, funct, target, values):
        ret = getattr(self, funct)(**values)
        r = requests.post(target, ret)
        return r

# Bridge Queue
    def BridgeQueue(self):
        pass

### Metodos Extra ###
# Invocacion rapida de print(colored('text','color')) req: termcolor
    def pc(self, text, color, printstamp=True):
        if printstamp:
            print(('[%s]: %s' % (time.strftime('%x %H:%M:%S'),
            colored('[%s]' % text, color))))
        else:
            print((colored(text, color)))
        log = '[%s]: %s' % (time.strftime('%x %H:%M:%S'), text)
        if color is 'red':
            logging.error(log)
        elif color is 'yellow':
            logging.warning(log)
        elif color is 'blue':
            logging.info(log)

    def writeConfig(self, key, values):
        config = configparser.RawConfigParser()
        config.read(r'config.ini')
        for v in values:
            config.set(key, v[0], v[1])
        with open(r'config.ini', 'wb') as configfile:
            config.write(configfile)

    def session_exec(self):
        self.session = Session(self.dbeng)
        tweets = self.orm.classes.tweets
        self.session.add(tweets(text='tweet de prueba', id_str='257460186',
            id_tweet=257460186, lang='es'))
        self.session.commit()


class Bridge(object):
    ini = ''
    cp = None
    queue = None
    errors = ''
    dbeng = None
    conn = None
    api = None
    services = []

    def __init__(self):
        self.ini = 'config.ini'
        self.cp = configparser.ConfigParser()
        self.cp.read(self.ini)
        self.errors = 'ERRORS-twistreapy'
        redcfg = self.cp['REDIS']
        self.queue = redis.Redis(host=redcfg['host'], port=redcfg['port'],
            decode_responses=True)
        #self.queue = redis.Redis(decode_responses=True)
        db = self.cp['DATABASE']
        self.connect_database('postgresql', db['user'], db['pass'], db['host'],
            db['name'])
        apicfg = self.cp['API']
        self.api = twitter.Api(apicfg['consumer_key'],
            apicfg['consumer_secret'], apicfg['access_token'],
            apicfg['access_token_secret'], sleep_on_rate_limit=True)
        app = Flask(__name__)

        @app.route("/get/status")
        def get_status():
            ret = {'running': False, 'rderrors': []}
            pid = '%s/%s.pid' % (self.cp.get('PID', 'dir'),
                self.cp.get('PID', 'name'))
            # Verifica si el archivo PID existe
            if os.path.exists(pid):
                with open(pid, 'r') as p:
                    ppid = int(p.readline())
                # Verifica si el PID se esta ejecutando
                if psutil.pid_exists(ppid):
                    ret['running'] = True
                    p = psutil.Process(ppid)
                    ret['since'] = datetime.datetime.fromtimestamp(
                        p.create_time()).strftime("%d-%m-%Y %H:%M:%S")
            # Chequear estado de REDIS
            try:
                self.queue.client_list()
            except redis.ConnectionError:
                ret['redis'] = False
            else:
                ret['redis'] = True
            # Recibir Errores en Queue
            if ret['redis']:
                try:
                    ret['rderrors'] = self.getErrors()
                except Exception as e:
                    ret['rderrors'] = ['%s' % e]
            return jsonify(ret)

        @app.route("/get/config.ini")
        def get_config():
            ret = {}
            for sect in self.cp.sections():
                ret[sect] = {}
                for t in list(self.cp[sect].items()):
                    # Fix: Convierte a listas los campos separados por coma
                    if t[0] == 'keywords' or t[0] == 'user_ids' or \
                    t[0] == 'entities':
                        ret[sect][t[0]] = ",".join(t[1].split(','))
                    else:
                        ret[sect][t[0]] = t[1]
            return jsonify(ret)

        @app.route("/get/log")
        def get_log():
            return self.readLog('output.log')

        @app.route("/clear/log")
        def clear_log():
            ret = {'status': self.clearLog('output.log')}
            return jsonify(ret)

        @app.route("/get/user_ids", methods=['GET', 'POST'])
        def get_user_ids():
            POST = request.get_json(force=True)
            ret = Twistreapy().convertNamesIds(**POST)
            return jsonify(ret)

        @app.route("/get/query/<query>")
        def get_query(query):
            cache = self.cacheRead(query, 'query')
            if cache:
                return jsonify(cache)
            ret = {}
            with open('query.json') as js:
                qs = json.load(js)
            if query in qs:
                res = self.raw_sql(qs[query])
                c = 0
                for row in res:
                    ret[c] = {}
                    for k, v in list(row.items()):
                        ret[c][k] = v
                    c += 1
            else:
                ret['error'] = True
            if len(ret) <= 1:
                ret = ret[0]
            self.cacheWrite(query, 'query', ret)
            return jsonify(ret)

        @app.route("/get/tsv/<query>")
        def get_tsv(query):
            ret = self.cacheRead(query, 'tsv')
            if ret:
                return Response(ret,
                    mimetype="text/tsv",
                    headers={"Content-disposition":
                    "attachment; filename=data.tsv"
                    })
            else:
                ret = ''
            with open('query.json') as js:
                qs = json.load(js)
            if query in qs:
                res = self.raw_sql(qs[query])
                # Headers
                if len(res) < 1:
                    return 'None'
                for h, v in list(res[0].items()):
                    ret += '%s\t' % h
                ret += '\n'
                # Content
                for row in res:
                    for k, v in list(row.items()):
                        if type(v) is FloatType:
                            ret += '%s\t' % '{0:g}'.format(float(v))
                        else:
                            ret += '%s\t' % v
                    ret += '\n'
            self.cacheWrite(query, 'tsv', ret)
            return Response(
                ret,
                mimetype="text/tsv",
                headers={"Content-disposition":
                    "attachment; filename=data.tsv"
                    }
                )

        @app.route("/get/json/<query>")
        def get_json(query):
            cache = self.cacheRead(query, 'json')
            if cache:
                return jsonify(json.dumps(cache))
            ret = []
            with open('query.json') as js:
                qs = json.load(js)
            if query in qs:
                res = self.raw_sql(qs[query])
                for row in res:
                    arr = {}
                    for k, v in list(row.items()):
                        arr[k] = v
                    ret.append(arr)
                self.cacheWrite(query, 'json', ret)
            else:
                ret['error'] = True
            return jsonify(json.dumps(ret))

        @app.route("/get/rates/<query>")
        def get_rates(query):
            ret = self.getRates()
            if query == 'json':
                return jsonify(ret)
            elif query == 'remaining':
                add = {}
                for r in ret:
                    add[r] = ret[r]['remaining']
                return jsonify(add)

        @app.route("/get/flare/v1/<query>")
        def get_flare_v1(query):
            cache = self.cacheRead(query, 'flare')
            if cache:
                return Response(cache,
                    mimetype="text/csv",
                    headers={"Content-disposition":
                    "attachment; filename=flare.csv"
                    })
            ret = ''
            with open('query.json') as js:
                qs = json.load(js)
            if query in qs:
                res = self.raw_sql(qs[query])
                if len(res) < 1:
                    return 'None'
                ### FLARE START
                base = 'flare'
                ret = 'id,value\n'
                ret += '%s,\n' % base
                #for k, v in [row.items() for row in res]:
                for row in res:
                    group, subgroup, name, value = ''
                    for k, v in list(row.items()):
                        if k == 'group':
                            group = v
                        elif k == 'subgroup':
                            subgroup = v
                        elif k == 'value':
                            value = '%s' % str(v)
                        elif k == 'name':
                            name = v
                    if not value and not name:
                        continue
                    if name and not value:
                        value = '0'
                    if subgroup and group:
                        ret += '%s.%s.%s.%s,%s' % (base, group, subgroup, name, value)
                    elif group:
                        ret += '%s.%s.%s,%s' % (base, group, name, value)

            else:
                ret = 'Query not found'
            return Response(ret,
                mimetype="text/csv",
                headers={"Content-disposition":
                "attachment; filename=flare.csv"
                })

        @app.route("/save/config.ini", methods=['GET', 'POST'])
        def save_config():
            POST = request.get_json(force=True)
            if 'csrfmiddlewaretoken' in POST:
                del POST['csrfmiddlewaretoken']
            if 'action' in POST:
                del POST['action']
            for t, c in list(POST.items()):
                y = dict(c)
                for k, v in list(y.items()):
                    self.cp.set(t, k, v)
            #self.cp.read_dict(POST)
            with open(self.ini, 'wb') as cfile:
                self.cp.write(cfile)
            #TODO: Tratar excepciones
            self.cp = configparser.ConfigParser()
            self.cp.read(self.ini)
            ret = {'message': 'Configuracion Guardada Exitosamente',
                'message_type': 'success'}
            return jsonify(ret)

        @app.route("/get/hashtags/count")
        def hashtag_count():
            q = 'select to_date(created_at, \'Dy mon DD HH24:MI:SS "+0000" YY\
YY\') as dia, count(*) as tweets from tweets group by dia;'
            ret = {}
            result = self.raw_sql(q)
            for row in result:
                ret[str(row['dia'])] = row['tweets']
            return jsonify(ret)

        @app.route("/service/twistreapy/start")
        def start_service():
            self.stop_tmux()
            self.start_tmux()
            time.sleep(1)
            return get_status()

        @app.route("/service/twistreapy/stop")
        def stop_service():
            self.stop_tmux()
            time.sleep(1)
            return get_status()

        @app.route("/service/redis/start")
        def start_redis():
            self.stop_tmux('redis')
            self.start_tmux(name='redis', command='redis-server')
            time.sleep(1)
            return get_status()

        @app.route("/search/tweets", methods=['GET', 'POST'])
        def search_tweets():
            if self.api.CheckRateLimit(
            'https://api.twitter.com/1.1/search/tweets.json').remaining <= 0:
                return jsonify({'error': True, 'message': 'Rate Limit'})
            POST = request.get_json(force=True)
            args = self.search_args(POST)
            try:
                search = self.api.GetSearch(**args)
            except:
                return jsonify({
                    'error': True,
                    'message': sys.exc_info()[0],
                    'message_type': 'danger'
                })
            if not len(search):
                return jsonify({
                    'message': '0 resultados encontrados',
                    'count': 0
                })
            ids = []
            for r in search:
                status = r.AsDict()
                self.queue.rpush('stream', json.dumps(status))
                ids.append(status.get('id'))
            ids = sorted(ids, key=int)
            ret = {
                'count': len(search),
                'since_id': ids[0],
                'max_id': ids[-1],
                'since': args.get('since', ''),
                'until': args.get('until', ''),
                'term': args.get('term', ''),
                'raw_query': args.get('raw_query', ''),
                'message': '%d Tweets Pusheados a Redis' % len(search)
            }
            return jsonify(ret)

        @app.route("/search/timeline", methods=['GET', 'POST'])
        def search_timeline():
            if self.api.CheckRateLimit(
    'https://api.twitter.com/1.1/statuses/user_timeline.json').remaining <= 0:
                return jsonify({'error': True, 'message': 'Rate Limit'})
            POST = request.get_json(force=True)
            args = self.timeline_args(POST)
            try:
                search = self.api.GetUserTimeline(**args)
            except:
                return jsonify({
                    'error': True,
                    'message': sys.exc_info()[0],
                    'message_type': 'danger'
                })
            if not len(search):
                return jsonify({
                    'message': '0 resultados encontrados',
                    'count': 0
                })
            ids = []
            for r in search:
                status = r.AsDict()
                self.queue.rpush('stream', json.dumps(status))
                ids.append(status.get('id'))
            ids = sorted(ids, key=int)
            ret = {
                'count': len(search),
                'since_id': ids[0],
                'max_id': ids[-1],
                'user_id': args.get('user_id', ''),
                'screen_name': args.get('screen_name', ''),
                'include_rts': args.get('include_rts', ''),
                'exclude_replies': args.get('exclude_replies', ''),
                'message': '%d Tweets Pusheados a Redis' % len(search)
            }
            return jsonify(ret)

        @app.route("/search/retweets", methods=['GET', 'POST'])
        def search_retweets():
            if self.api.CheckRateLimit(
    'https://api.twitter.com/1.1/statuses/user_timeline.json').remaining <= 0:
                return jsonify({'error': True, 'message': 'Rate Limit'})
            POST = request.get_json(force=True)
            args = self.retweets_args(POST)
            try:
                search = self.api.GetRetweets(**args)
            except:
                return jsonify({
                    'error': True,
                    'message': sys.exc_info()[0],
                    'message_type': 'danger'
                })
            if not len(search):
                return jsonify({
                    'message': '0 resultados encontrados',
                    'count': 0
                })
            ids = []
            for r in search:
                status = r.AsDict()
                self.queue.rpush('stream', json.dumps(status))
                ids.append(status.get('id'))
            ids = sorted(ids, key=int)
            ret = {
                'count': len(search),
                'tweet_id': args.get('statusid', ''),
                'message': '%d Tweets Pusheados a Redis' % len(search)
            }
            return jsonify(ret)

        @app.route("/search/ffs", methods=['GET', 'POST'])
        def search_ffs():
            POST = request.get_json(force=True)
            user_id = POST.get('user_id', False)
            if user_id is False:
                return jsonify({
                    'error': True,
                    'message': 'User_ID Nulo o Invalido',
                    'message_type': 'danger'
                })
            api = Twistreapy()
            self.services.append(mp.Process(
                name='ffs_%s' % str(user_id),
                target=api.followersSingle,
                args=(user_id, )
            ))
            self.services[-1].daemon = True
            self.services[-1].start()
            return jsonify({
                'error': False,
                'message': 'Servicio Iniciado Correctamente',
                'message_type': 'success'
            })
        app.run(host='0.0.0.0')

    def getError(self):
        item = self.queue.lpop(self.errors)
        return item

    def getErrors(self):
        llen = self.queue.llen(self.errors)
        count = 0
        ret = []
        if llen > 0:
            while count < llen:
                ret.append(self.getError())
                count += 1
        return ret

    def getRates(self):
        ret = {}
        with open('rates.json', 'r') as rfile:
            calls = json.load(rfile)
        for call in calls:
            res = self.api.CheckRateLimit(calls[call])
            ret[call] = {
                'limit': res.limit,
                'remaining': res.remaining,
                'reset': datetime.datetime.fromtimestamp(res.reset).strftime(
                    '%H:%M:%S')
            }
        return ret

    def connect_database(self, engine, user, passw, host, name):
        self.dbeng = create_engine('%s://%s:%s@%s/%s' % (engine, user, passw,
            host, name))
        self.conn = self.dbeng.connect()

    def raw_sql(self, sql):
        s = text(sql)
        return self.conn.execute(s).fetchall()

    def stop_tmux(self, name='twistreapy'):
        tmux = libtmux.Server()
        if tmux.has_session(name):
            tmux.kill_session(name)
            return True
        return False

    def search_args(self, POST):
        args = {
            'term': POST.get('term', None),
            'raw_query': POST.get('raw_query', None),
            'since_id': POST.get('since_id', None),
            'max_id': POST.get('max_id', None),
            'until': POST.get('until', None),
            'since': POST.get('since', None),
            'count': 200,
            'lang': POST.get('lang', None),
            'result_type': POST.get('result_type', 'mixed')
        }
        for k, v in list(args.items()):
            if v == '':
                args[k] = None
        return args

    def timeline_args(self, POST):
        args = {
            'user_id': POST.get('user_id', None),
            'screen_name': POST.get('screen_name', None),
            'since_id': POST.get('since_id', None),
            'max_id': POST.get('max_id', None),
            'include_rts': POST.get('include_rts', True),
            'exclude_replies': POST.get('exclude_replies', False),
            'count': 200,
            'trim_user': False
        }
        for k, v in list(args.items()):
            if v == '':
                args[k] = None
        return args

    def retweets_args(self, POST):
        args = {
            'statusid': POST.get('tweet_id', None),
            'count': 100,
            'trim_user': False
        }
        return args

    def start_tmux(
    self, name='twistreapy',
    path='', venv='../venv/bin/activate',
    command='python __main__.py start'):
        self.stop_tmux(name)
        tmux = libtmux.Server()
        #tmux.remove_environment('PATH')
        #tmux.remove_environment('VIRTUAL_ENV')
        if not path or path == '':
            path = os.path.dirname(os.path.realpath(__file__))
        session = tmux.new_session(name, True, False, path)
        pane = session.attached_pane
        pane.send_keys('source %s' % venv)
        pane.send_keys(command)
        return True

    def readLog(self, log):
        with open(log, 'r') as lf:
            return lf.read()

    def clearLog(self, log):
        logfile = self.readLog(log)
        with open(r'/home/gabriel/pst/twistreapy/src/logs/%s.log' %
        time.strftime("%d-%m-%y", time.gmtime()), 'w') as f:
            f.write(logfile)
        with open(log, 'w'):
            pass
        return True

    def cacheRead(self, query, ext):
        name = 'cache/%s.%s' % (query, ext)
        try:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(name))
        except OSError:
            print(('Archivo Inexistente. Devolviendo Query para %s.%s' % (
                query, ext)))
            return False
        if mtime > datetime.datetime.now() - datetime.timedelta(hours=3):
            with open(name, 'r') as cache:
                print(('Devolviendo Cache para %s.%s' % (query, ext)))
                if ext == 'json' or ext == 'query':
                    return json.load(cache)
                else:
                    return cache.read()
        else:
            print(('Devolviendo Query para %s.%s' % (query, ext)))
            return False

    def cacheWrite(self, query, ext, ret):
        name = 'cache/%s.%s' % (query, ext)
        with open(name, "w") as cache:
            if ext == 'tsv':
                cache.write('%s' % ret.encode('utf-8'))
            if ext == 'json' or ext == 'query':
                cache.write(json.dumps(ret))
            #TODO handle exceptions
        return True