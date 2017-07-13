import sys
from twistrea import Twistreapy, Bridge


api = Twistreapy()


def reload_configs():
    global api
    api = None
    api = Twistreapy()


def pressenter():
    print("\n")
    try:
        eval(input("Press Enter to continue..."))
    except SyntaxError:
        pass


def show_tfl():
    api.pc('[Track] List. Include @Mentions, #Hastags and Expressions: ',
        'blue')
    for kw in api.keywords:
        print(kw)
    api.pc('[Follow] List. User IDs to Follow: ', 'green')
    for ui in api.user_ids:
        print(ui)
    api.pc('Selected Languages: ', 'blue')
    for ln in api.langs:
        print(ln)
    pressenter()


def show_apicfg():
    api.pc('[API] Configuration Options', 'blue')
    for opt in api.apicfg:
        print((opt + ': ' + api.apicfg[opt]))
    pressenter()


def convert(val):
    try:
        exec('convert_%s()' % (val))
    except:
        api.pc('convert_%s() not found' % (val), 'red')


def convert_names():
    api.pc("Converting Screen Names to UID's", 'blue')
    api.convertScreenNames()
    #api.writeConfig('REDIS', [('host', 'test'), ('port', '1234')])
    pressenter()


def start():
    api.Start()


def startbridge():
    Bridge()


sarg = ''
try:
    if len(sys.argv) > 2:
        steps = len(sys.argv) - 2
        index = 2
        while steps > 0:
            sarg += sys.argv[index]
            if steps > 0:
                sarg += ', '
            steps -= 1
            index += 1
        run = '%s("%s")' % (sys.argv[1], sarg)
    else:
        run = '%s()' % (sys.argv[1])
    exec(run)
except NameError:
    api.pc("Unknown parameter: '%s'" % (sys.argv[1]), 'red')
except IndexError:
    api.pc("Starting default 'start' command", 'red')
    start()
except TypeError as e:
    api.pc(e, 'red')
    api.pc('Invalid or Missing Arguments?', 'red')