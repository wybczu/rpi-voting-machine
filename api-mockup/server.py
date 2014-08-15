#!/usr/bin/env python
# -*- coding: utf8 -*-

import json
from flask import Flask, request
from flask.ext.restful import Resource, Api

app = Flask(__name__)
api = Api(app)


class Votes(Resource):

    def post(self):
        print json.dumps(request.form, sort_keys=True, indent=4, separators=(',', ': '))


api.add_resource(Votes, '/vote')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
