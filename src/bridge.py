# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from twistrea import *


class Bridge(twistrea.Twistreapy):

    def __init__(self):
        super(Bridge, self).__init__()

        self.pc('Starting ManageCenter Bridge Server', 'blue')
        app = Flask(__name__)

        @app.route("/")
        def hello():
            return "Hello World!"

        @app.route("/get/config.ini")
        def get_config():
            ret = {}
            for sect in self.cp.sections():
                ret[sect] = {}
                for t in list(self.cp[sect].items()):
                    # Fix: Convierte a listas los campos separados por coma
                    if t[0] == 'keywords' or t[0] == 'user_ids' or \
                    t[0] == 'entities':
                        ret[sect][t[0]] = ",".join(t[1].split(','))
                    else:
                        ret[sect][t[0]] = t[1]
            return jsonify(ret)

        @app.route("/save/config.ini", methods=['GET', 'POST'])
        def save_config():
            POST = request.get_json(force=True)
            if 'csrfmiddlewaretoken' in POST:
                del POST['csrfmiddlewaretoken']
            if 'action' in POST:
                del POST['action']
            for t, c in list(POST.items()):
                y = dict(c)
                for k, v in list(y.items()):
                    self.cp.set(t, k, v)
            with open(self.ini, 'wb') as cfile:
                self.cp.write(cfile)
            #TODO: Tratar excepciones
            ret = {'message': 'Configuracion Guardada Exitosamente',
                'message_type': 'success'}
            return jsonify(ret)

        app.run()