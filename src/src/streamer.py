import json


def streamFilter(track, api, db):
    print('Starting streaming service')
    for status in api.GetStreamFilter(track=track):
        print('New Tweet Pushed to Redis')
        db.rpush(track, json.dumps(status))