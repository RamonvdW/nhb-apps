# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.views.generic import View
from Privacy.operations import get_verklaring_doc

TEMPLATE_PRIVACY_VERKLARING = 'privacy/verklaring.dtl'


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
