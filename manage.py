#!/bin/bash
# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# this line + shebang ensures python is taken from the user's PATH
# python sees this as a string and ignores it
# note: -u = unbuffered stdout/stderr
"exec" "python3" "-u" "$0" "$@"

from django.core.management import execute_from_command_line
from TestHelpers.e2estatus import validated_templates, included_templates, consistent_email_templates
from traceback import StackSummary
from pathlib import Path
import sys
import os

"""
    Django's command-line utility for administrative tasks.
"""


def report_validated_templates():
    """ Report which templates are not covered by a test that invokes assert_html_ok """

    # do something special for a "test all" run
    if len(validated_templates) > 100:          # pragma: no branch
        # for dtl in validated_templates:
        #     print('Validated template: %s' % repr(dtl))
        # # for

        for dtl in Path().rglob('*.dtl'):
            dtl_str = str(dtl)
            is_email_template = '/templates/email_' in dtl_str
            dtl_str = dtl_str[dtl_str.find('/templates/')+11:]
            if dtl_str not in included_templates:       # pragma: no cover
                if dtl_str not in validated_templates:
                    if is_email_template:
                        print('[WARNING] Missing assert_email_html_ok coverage for template %s' % repr(dtl_str))
                    else:
                        print('[WARNING] Missing assert_html_ok coverage for template %s' % repr(dtl_str))

                if is_email_template and dtl_str not in consistent_email_templates:
                    print('[WARNING] Missing assert_consistent_email_html_text coverage for e-mail template %s' % repr(dtl_str))
        # for


def my_format(self):            # pragma: no cover
    """ variant of StackSummary.format that skips all django site-package files in the output
        so focus is on the application source files. This saves ~75% of the output.
    """
    suppress = '  ...\n'
    result = []
    for frame in self:
        if '/site-packages/django/' not in frame.filename:
            row = list()
            row.append('  File "{}", line {}, in {}\n'.format(
                frame.filename, frame.lineno, frame.name))
            if frame.line:
                row.append('    {}\n'.format(frame.line.strip()))
            if frame.locals:
                for name, value in sorted(frame.locals.items()):
                    row.append('    {name} = {value}\n'.format(name=name, value=value))
            result.append(''.join(row))
        else:
            if len(result) == 0 or result[-1] != suppress:
                result.append(suppress)
    # for
    return result


def main():
    # eigen formatteer functie voor de stack trace, zodat we alleen nuttige regels kunnen tonen
    StackSummary.format = my_format

    try:
        # print a clear separator on the terminal when using runserver or test
        stars = None
        if "runserver" in sys.argv or ("test" in sys.argv and "--noinput" not in sys.argv):
            # avoid double line when runserver starts a child process
            if "DJANGO_SETTINGS_MODULE" not in os.environ:  # pragma: no branch
                stars = "*" * 30
                print("\n%s START OF RUN %s\n" % (stars, stars))

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhbapps.settings')
        execute_from_command_line(sys.argv)

        report_validated_templates()

        if stars:                   # pragma: no cover
            print("\nDone!")
    except (KeyboardInterrupt, SystemExit):       # pragma: no cover
        print('\nInterrupted!')
        sys.exit(3)                 # allows test suite to detect test abort


if __name__ == '__main__':  # pragma: no branch
    main()

# end of file
