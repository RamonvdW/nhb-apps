# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import esprima


def validate_javascript(script):
    """ use ESprima to validate the javascript / ecmascript """

    issues = list()

    # strip <script src=".." type="..">
    script = script[script.find('>' ) +1:]

    # strip </script>
    script = script[:script.find('</script>')]

    if script:
        # print('esprima: %s' % repr(script))
        strict = '"use strict";'

        failure = False
        try:
            result = esprima.parseScript(strict + script)
        except esprima.Error:                       # pragma: no cover
            failure = True
        else:
            if result.errors:                       # pragma: no cover
                failure = True

        if failure:                                 # pragma: no cover
            # make "Error in line 1" more useful
            script = script.replace(';', ';\n')

            add_snippet = True
            try:
                result = esprima.parseScript(strict + script)
            except esprima.Error as exc:
                issues.append("Exception in script: %s" % str(exc))
            else:
                if result.errors:
                    issues.append("Error in script: %s" % repr(result.errors))
                else:
                    # no error in the readable script!
                    issues.append('Could not duplicate script error after making readable')
                    add_snippet = False

            if add_snippet:
                issues.append("Snippet:")
                # avoid empty line at end
                if script[-1] == '\n':
                    script = script[:-1]
                nr = 0
                for line in script.split('\n'):
                    nr += 1
                    issues.append('  %s: %s' % (nr, line))
                # for

    return issues

# end of file
