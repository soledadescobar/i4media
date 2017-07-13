import json
import requests

url = 'http://localhost/python/post.php'


def datapost(postdata, keyname):
    response = requests.post(url, data=postdata)
    if(response.status_code == 200):
        print(('Datapost Response OK for list ' + keyname))


def popblock(keys, db):
    x = 0
    name = ''
    #item posicion 0 = nombre de lista; posicion 1 = json
    for item in db.blpop(keys, 0):
        if(x > 0):
            datapost(json.loads(item), name)
        else:
            name = item
        x += 1


def poploop(keys, db):
    print(('Starting PopLoop Service for key: ' + keys))
    while True:
        popblock(keys, db)