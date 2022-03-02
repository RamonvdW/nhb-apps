# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import sys

"""
    small utility to number the test cases
    used in combination with Django manage.py test -v
"""

number = 0
for line in sys.stdin:
    if line.startswith('test_'):
        number += 1
        print(number, line.rstrip())
    else:
        print(line.rstrip())
# for

# end of file
