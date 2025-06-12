# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Site.js_cov.find_js import JsCovFind
import json

"""
    This file is loaded by TestHelper/browser_test.py to save or import the collected coverage data
"""

JS_COV_FNAME = '/tmp/browser_js_cov.json'


def save_the_data(data):
    with open(JS_COV_FNAME, 'w') as f:
        f.write(json.dumps(data) + '\n')
        f.close()
    # with

    # trigger the coverage plugin for all JS files
    JsCovFind(data)


def import_the_data():
    with open(JS_COV_FNAME, 'r') as f:
        json_data = f.read()
    # with
    data = json.loads(json_data)

    # trigger the coverage plugin for all JS files
    JsCovFind(data)


# end of file
