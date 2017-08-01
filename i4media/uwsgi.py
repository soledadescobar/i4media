#  from .logger import *
from .restapi import RestApiBridge


rest = RestApiBridge()
rest.apps()

application = rest.app

rest.app.logger.info('UWSGI Application Started')
