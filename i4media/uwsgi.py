from .logger import *
import i4media.restapi


rest = i4media.restapi.RestApiBridge()
rest.apps()
