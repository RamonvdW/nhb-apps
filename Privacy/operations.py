# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils.safestring import mark_safe

# verklaring is een lijst van tuples: (layout_code, inhoud)
# waarbij layout_code kan zijn:
# h1, h2, ul+, ul-, li
verklaring = []


def laad_privacyverklaring(fpath: str):
    with open(fpath, 'r') as f:
        lines = f.readlines()

    global verklaring

    # eerste regel is de titel
    verklaring = list()
    verklaring.append(('h1', lines.pop(0)))

    level = 0

    for regel in lines:
        regel = regel.strip()

        if regel == '':
            if level == 2:
                verklaring.append(('**-', ''))
                level = 1

            if level == 1:
                verklaring.append(('*-', ''))
                level = 0

            verklaring.append(('br', ''))

        elif regel[:1] == '=':
            if level == 2:
                verklaring.append(('**-', ''))
                level = 1

            if level == 1:
                verklaring.append(('*-', ''))
                level = 0

            verklaring.append(('h2', regel[1:]))

        elif regel[:2] == '**':
            if level == 1:
                # pas de voorgande * aan
                tup = verklaring.pop(-1)
                verklaring.append(('**+', tup[1]))
                level = 2

            verklaring.append(('*', regel[2:]))

        elif regel[:1] == '*':
            if level == 2:
                verklaring.append(('**-', ''))
                level = 1

            if level == 0:
                verklaring.append(('*+', ''))
                level = 1

            verklaring.append(('*', regel[1:]))

        else:
            if level == 2:
                verklaring.append(('**-', ''))
                level = 1

            if level == 1:
                verklaring.append(('*-', ''))
                level = 0

            pos = regel.find('%link%')
            if pos > 0:
                verklaring.append(('p1', regel[:pos]))

                pos_end = regel.find(' ', pos)
                spl = regel[pos+6:pos_end]
                spl = spl.split('%')

                verklaring.append(('a1', spl[1]))
                verklaring.append(('a2', spl[0]))

                verklaring.append(('p2', regel[pos_end:]))
            else:
                verklaring.append(('p', regel))
    # for

    while verklaring[-1] == ('br', ''):
        verklaring.pop(-1)
    # while


def get_verklaring_doc():
    global verklaring

    # eerste keer automatisch inladen
    if len(verklaring) == 0:
        fpath = os.path.join(settings.INSTALL_PATH, settings.PRIVACYVERKLARING_FILE)
        laad_privacyverklaring(fpath)

    # for tup in verklaring:
    #     print(repr(tup[0]), repr(tup[1][:20]))
    # # for

    return verklaring


def clear_verklaring():
    # wordt gebruikt door de test suite
    global verklaring
    verklaring = []


# end of file
