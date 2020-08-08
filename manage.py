#!/bin/bash
# -*- coding: utf-8 -*-

# this line + shebang ensures python is taken from the user's PATH
# python sees this as a string and ignores it
"exec" "python" "$0" "$@"

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Django's command-line utility for administrative tasks.
"""

import os
import sys
from django.core.management import execute_from_command_line


def main():
    # print a clear separator on the terminal when using runserver or test
    stars = None
    if "runserver" in sys.argv or ("test" in sys.argv and "--noinput" not in sys.argv):
        # avoid double line when runserver starts a child process
        if "DJANGO_SETTINGS_MODULE" not in os.environ:      # pragma: no branch
            stars = "*" * 30
            print("\n%s START OF RUN %s\n" % (stars, stars))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhb-apps.settings')
    execute_from_command_line(sys.argv)

    if stars:
        print("\nDone!")


if __name__ == '__main__':      # pragma: no branch
    main()

# end of file

