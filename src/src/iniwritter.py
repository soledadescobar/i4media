# -*- coding: utf-8 -*-
import configparser
cp = configparser.ConfigParser()
cp['API'] = {'consumer_key': 'Gmfyhl7Gj7hR8QsoHXnac3T0G',
    'consumer_secret': 'bWg0aOtWEN4iIIkwFkuwI9WXpqegC4kxwj6T6au2cwV6m6FnBy',
    'access_token': '3343144691-amaGCBTVaeLpb5yelml70xWXArzo7r1kwMf1yRj',
    'access_token_secret': '9b6W2ZFHIWk7svW54gAslxSJ7CBWiAHOKR5RBQ3jKLsae'}

with open('config.ini', 'w') as cfg:
    cp.write(cfg)