import sys
from ext import ShellApi


if len(sys.argv) > 1:
    api = ShellApi(sys.argv[1])
else:
    api = ShellApi()
api.searchkeywords()
