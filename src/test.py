from twistrea import Twistreapy


api = Twistreapy()

tweets = api.orm.classes.tweets

for key in list(tweets.__dict__.keys()):
    if not key.startswith('_'):
        exec('print((tweets.%s.cast))' % key)
