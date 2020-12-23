#!/bin/bash
# -*- coding: utf-8 -*-

# this line + shebang ensures python is taken from the user's PATH
# python sees this as a string and ignores it
"exec" "python" "$0" "$@"

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management import execute_from_command_line
from Overig.e2estatus import validated_templates, included_templates
from pathlib import Path
import sys
import os

"""
    Django's command-line utility for administrative tasks.
"""


def report_validated_templates():
    """ Report which templates are not covered by a test that invokes assert_html_ok """

    if len(validated_templates) > 100:      # only do this on a "test all" run
        # for dtl in validated_templates:
        #     print('Validated template: %s' % repr(dtl))
        # # for

        for dtl in Path().rglob('*.dtl'):
            dtl_str = str(dtl)
            dtl_str = dtl_str[dtl_str.find('/templates/')+11:]
            if dtl_str not in validated_templates and dtl_str not in included_templates:
                print('[WARNING] Missing assert_html_ok coverage for template %s' % repr(dtl_str))
        # for


def main():
    # print a clear separator on the terminal when using runserver or test
    stars = None
    if "runserver" in sys.argv or ("test" in sys.argv and "--noinput" not in sys.argv):
        # avoid double line when runserver starts a child process
        if "DJANGO_SETTINGS_MODULE" not in os.environ:  # pragma: no branch
            stars = "*" * 30
            print("\n%s START OF RUN %s\n" % (stars, stars))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhb-apps.settings')
    execute_from_command_line(sys.argv)

    report_validated_templates()

    if stars:
        print("\nDone!")


if __name__ == '__main__':  # pragma: no branch
    main()

# end of file
