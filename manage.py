#!/bin/bash
# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# this line + shebang ensures python is taken from the user's PATH
# python sees this as a string and ignores it
# note: -u = unbuffered stdout/stderr
"exec" "python3" "-u" "$0" "$@"     # noqa

from django.core.management import execute_from_command_line
from Site.core.main_exceptions import SpecificExitCode
from TestHelpers.template_status import end_of_run
from traceback import StackSummary
import sys
import os

"""
    Django's command-line utility for administrative tasks.
"""


def my_format(self, colorize=None):            # pragma: no cover
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
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Site.settings')
        execute_from_command_line(sys.argv)
        end_of_run()

    except SpecificExitCode as exc:
        code = exc.args[0]
        print('\nSpecific exit code: %s' % repr(code))
        sys.exit(code)

    except (KeyboardInterrupt, SystemExit):       # pragma: no cover
        print('\nInterrupted!')
        sys.exit(3)                 # allows test suite to detect test abort


if __name__ == '__main__':  # pragma: no branch
    main()

# end of file
