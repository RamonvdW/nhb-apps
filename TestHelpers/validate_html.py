# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import subprocess
import tempfile
import vnujar


VALIDATE_IGNORE = (
    'info warning: The “type” attribute is unnecessary for JavaScript resources.',
    'error: Attribute “loading” not allowed on element “img” at this point.'  # too new
)


def validate_html(html):                # pragma: no cover
    """ Run the HTML5 validator """
    issues = list()

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as tmp:
        tmp.write(html)
        tmp.flush()

        # credits to html5validator
        vnu_jar_location = vnujar.__file__.replace('__init__.pyc', 'vnu.jar').replace('__init__.py', 'vnu.jar')
        with subprocess.Popen(["java", "-jar", vnu_jar_location, tmp.name], stderr=subprocess.PIPE) as proc:
            proc.wait(timeout=5)
            # returncode is 0 als er geen problemen gevonden zijn
            if proc.returncode:
                lines = html.splitlines()

                # feedback staat in stderr
                msg = proc.stderr.read().decode('utf-8')

                # remove tmp filename from error message
                msg = msg.replace('"file:%s":' % tmp.name, '')
                for issue in msg.splitlines():
                    # extract location information (line.pos)
                    spl = issue.split(': ')  # 1.2091-1.2094
                    locs = spl[0].split('-')
                    l1, p1 = locs[0].split('.')
                    l2, p2 = locs[1].split('.')
                    if l1 == l2:
                        l1 = int(l1)
                        p1 = int(p1)
                        p2 = int(p2)
                        p1 -= 20
                        if p1 < 1:
                            p1 = 1
                        p2 += 20
                        line = lines[l1 - 1]
                        context = line[p1 - 1:p2]
                    else:
                        context = ''
                        pass
                    clean = ": ".join(spl[1:])
                    if clean not in issues:
                        if clean not in VALIDATE_IGNORE:
                            clean += " ==> %s" % context
                            issues.append(clean)
                # for

    # tmp file is deleted here
    return issues

# end of file
