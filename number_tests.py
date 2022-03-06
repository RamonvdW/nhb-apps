# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import sys
import datetime

"""
    small utility to number the test cases
    used in combination with Django manage.py test -v
"""

start = datetime.datetime.now()
number = 0
for line in sys.stdin:
    if line.startswith('test_'):
        number += 1

        elapsed = datetime.datetime.now() - start
        elapsed = datetime.timedelta(seconds=elapsed.seconds)   # drop milliseconds (round down)
        time_str = str(elapsed)[-5:]    # mm:ss

        print(number, time_str, line.rstrip())
    else:
        print(line.rstrip())
# for

# end of file
