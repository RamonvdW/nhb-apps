# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
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
expected = 0
format_str = '%d / %d'

for line in sys.stdin:

    if line.startswith('test_') or '.js_tests.test_' in line:
        number += 1

        elapsed = datetime.datetime.now() - start
        elapsed = datetime.timedelta(seconds=elapsed.seconds)   # drop milliseconds (round down)
        time_str = str(elapsed)[-5:]    # mm:ss

        if expected > 1:
            if number == expected:
                perc_str = '99.99'
            else:
                perc_str = '%.2f' % ((number * 100) / expected)
            print((format_str + ' (%5s%%) %s %s') % (number, expected, perc_str, time_str, line.rstrip()))
        else:
            print('%s %s %s' % (number, time_str, line.rstrip()))

    elif line.startswith('Found '):
        if ' test(s).' in line:
            # line = "Found 123 test(s).\n"
            nr = int(line.split(' ')[1])
            expected = number + nr
            expected_len = len(str(expected))
            format_str = '%%%dd / %%%dd' % (expected_len, expected_len)

        print(line.rstrip())
    else:
        print(line.rstrip())
# for

# end of file
