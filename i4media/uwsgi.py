from .logger import *
from .restapi import RestApiBridge


rest = RestApiBridge()
rest.apps()
app = rest.app

