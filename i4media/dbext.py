from config import *
from sqlalchemy import *
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql import func
import sqlalchemy.ext
from sqlalchemy.sql import text


connection_string = '%s://%s:%s@%s/%s' % (
    DB_ENGINE, DB_USER, DB_PASS, DB_HOST, DB_NAME)


# DATABASE CONNECT
def connect_database():
    global dbeng
    global conn
    global orm
    # Create the automap object
    orm = automap_base()
    # Create the DB Engine
    dbeng = create_engine(connection_string, pool_size=30, max_overflow=100, pool_timeout=60)
    # Reflect actual's database objects
    orm.prepare(dbeng, reflect=True)
    # Connect
    conn = dbeng.connect()


def session_start():
    global session
    if not dbeng:
        connect_database()
    session = Session(dbeng)


def session_add(add):
    global session
    session.add(add)


def session_commit():
    global session
    try:
        session.commit()
    except sqlalchemy.exc.DBAPIError as e:
        # LOG THE ERROR HERE
        return False
    return True


def raw_sql(sql):
    try:
        global conn
        if conn:
            pass
    except NameError:
        connect_database()
    s = text(sql)
    return conn.execute(s).fetchall()


def insert_tweet(tweet, id_user=None):
    # Moving the ID to the field id_tweet
    tweet['id_tweet'] = tweet.pop('id')
    # Loading tweets model
    tweet_model = orm.classes.tweets
    # Carga de Entities
    if 'entities' in tweet:
        for ent in GLOBAL_ENTITIES:
            if ent in tweet['entities']:
                insert_entity(('tweet', tweet['id_tweet'], ent),
                                tweet['entities'][ent])
    # Carga alternativa de entities
    for ent in GLOBAL_ENTITIES:
        if ent in tweet:
            insert_entity(
                ('tweet', tweet['id_tweet'], ent),
                tweet[ent]
            )
    if tweet.get('user', False):
        # Cargo los datos del usuario
        tweet['id_user'] = tweet['user']['id']
        insert_userdata(tweet['user'])
    elif id_user:
        tweet['id_user'] = id_user
    else:
        return False
    # Por cada campo de la tabla tweets, busco el mismo campo en el objeto
    # tweet recibido y lo cargo al al dict para insertar
    add = {}
    for key in list(tweet_model.__dict__.keys()):
        if key in tweet:
            add[key] = tweet.get(key)
    session_start()
    session_add(tweet_model(**add))
    session_commit()
    return True


def insert_userdata(user):
    session_start()
    user['id_user'] = user.pop('id')
    add = {}
    if 'status' in user:
        insert_tweet(user['status'], user['id_user'])
    user_model = orm.classes.users
    for key in list(user_model.__dict__.keys()):
        if key in user:
            add[key] = user.get(key)
    session_add(user_model(**add))
    return session_commit()


## Inserta lista de objetos twitter user
def insert_user_list(userlist):
    for user in userlist:
        insert_userdata(user)


def insert_ffs(user_id, followers, friends):
    session_start()
    add = {}
    ff_model = orm.classes.friendfollower
    add['user_id'] = user_id
    add['followers'] = followers
    add['followers_count'] = len(followers)
    add['friends'] = friends
    add['friends_count'] = len(friends)
    add['created'] = func.now()
    session_add(ff_model(**add))
    session_commit()


### Inserta un objeto relacionado a un id_tweet
# obj = ( objeto_padre, id_objeto_padre, nombre_entiedad)
# cont = contenido de la entidad
def insert_entity(obj, cont):
    if not cont:
        return False
    for c in cont:
        if not hasattr(c, 'get'):
            return False
        exec("add = {'id_%s': %s}" % (obj[0], obj[1]))
        if 'id' in c:
            exec("c['id_%s'] = c.pop('id')" % obj[2])
        exec("entity_model = orm.classes.%s" % (obj[2], obj[2]))
        for key in list(entity_model.__dict__.keys()):
            if key in c:
                add[key] = c.get(key)
        if len(add) > 0:
            session_start()
            session_add(entity_model(**add))
            return session_commit()
    return False
