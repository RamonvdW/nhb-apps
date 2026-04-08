# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.views.generic import View
from django.utils.safestring import mark_safe

TEMPLATE_PRIVACY_VERKLARING = 'privacy/verklaring.dtl'


# verklaring is een lijst van tuples: (layout_code, inhoud)
# waarbij layout_code kan zijn:
# h1, h2, ul+, ul-, li
verklaring = []


def laad_privacyverklaring(fpath: str):
    lines = open(fpath, 'r').readlines()

    global verklaring

    # eerste regel is de titel
    verklaring = list()
    verklaring.append(('h1', lines.pop(0)))

    level = 0

    for regel in lines:
        regel = regel.strip()

        if regel == '':
            while level > 0:
                level -= 1
                verklaring.append(('ul-', ''))
            # while

            verklaring.append(('br', ''))

        elif regel[:1] == '=':
            while level > 0:
                level -= 1
                verklaring.append(('ul-', ''))
            # while

            verklaring.append(('h2', regel[1:]))

        elif regel[:2] == '**':
            if level == 1:
                level = 2
                verklaring.append(('ul+', ''))

            verklaring.append(('li', regel[2:]))

        elif regel[:1] == '*':
            if level == 2:
                verklaring.append(('ul-', ''))
                level = 1

            if level == 0:
                verklaring.append(('ul+', ''))
                level = 1

            verklaring.append(('li', regel[1:]))

        else:
            while level > 0:
                level -= 1
                verklaring.append(('ul-', ''))
            # while

            pos = regel.find('%link%')
            if pos > 0:
                pos_end = regel.find(' ', pos)
                print(pos, pos_end)
                spl = regel[pos+6:pos_end]
                spl = spl.split('%')
                print(spl)

                a_tag = '<a href="%s">%s</a>' % (spl[1], spl[0])

                regel = regel[:pos] + a_tag + regel[pos_end:]

                regel = mark_safe(regel)

            verklaring.append(('p', regel))
    # for

    while verklaring[-1] == ('br', ''):
        verklaring.pop(-1)
    # while


def get_verklaring_doc():
    global verklaring

    # for tup in verklaring:
    #     print(repr(tup[0]), repr(tup[1][:20]))
    # # for

    return verklaring


class VerklaringView(View):

    """ Django class-based view voor de Privacyverklaring

        De verklaring is een apart document op de server dat als een losse html pagina aangeboden wordt.
    """

    @staticmethod
    def get(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is """
        context = {
            'document': get_verklaring_doc(),
        }
        return render(request, TEMPLATE_PRIVACY_VERKLARING, context)


# end of file
