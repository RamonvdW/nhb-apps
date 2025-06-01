# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import json

"""
    This file is loaded by TestHelper/browser_test.py to save the collected coverage data
"""


def save_the_data(data):
    fname = '/tmp/browser_js_cov.json'
    with open(fname, 'w') as f:
        f.write(json.dumps(data) + '\n')
        f.close()
    # with


# end of file
