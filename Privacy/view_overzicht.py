# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.views.generic import TemplateView

TEMPLATE_PRIVACY_OVERZICHT = 'privacy/overzicht.dtl'


class OverzichtView(TemplateView):

    """ Django class-based view voor de openbare overzichtspagina over Privacy """

    # class variables shared by all instances
    template_name = TEMPLATE_PRIVACY_OVERZICHT

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_privacyverklaring'] = settings.PRIVACYVERKLARING_URL

        context['email_bb'] = settings.EMAIL_BONDSBUREAU
        context['url_email_bb'] = 'mailto:' + settings.EMAIL_BONDSBUREAU

        context['kruimels'] = (
            (None, 'Privacy'),
        )

        return context

# end of file
