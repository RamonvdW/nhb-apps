# -*- coding: utf-8 -*-
#
#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.utils import timezone
from django.views.generic import View
from GoogleDrive.models import Transactie
from GoogleDrive.operations.authenticatie import handle_authentication_response
from datetime import timedelta


class OAuthWebhookView(View):

    """ In deze view komen de webhook aanroepen terecht
        We sturen illegale verzoeken weg.
    """

    @staticmethod
    def get(request, *args, **kwargs):

        uri = request.get_full_path()
        #print('uri: %s' % repr(uri))

        # get the query parameters
        state = request.GET.get('state', None)
        if not state:
            raise Http404('Bad request')

        code = request.GET.get('code', None)        # authorization code with typical lifetime of 10 minutes
        error = request.GET.get('error', None)

        # security: filter onvolledige aanroepen zonder database query
        if not (error or code):
            raise Http404('Onvolledig verzoek')

        age_filter = timezone.now() - timedelta(days=3)
        try:
            transactie = (Transactie
                          .objects
                          .exclude(when__lt=age_filter)
                          .exclude(has_been_used=True)
                          .filter(unieke_code=state)
                          .first())
        except Transactie.DoesNotExist:
            transactie = None

        if not transactie:
            raise Http404('Onbekend verzoek')

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        transactie.has_been_used = True
        transactie.log += "[%s] Webhook aanroep: %s\n" % (stamp_str, uri)
        transactie.save(update_fields=['log', 'has_been_used'])

        token = handle_authentication_response(uri)
        if not token:
            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            transactie.log += "[%s] Geen bruikbaar token of geen refresh token)\n" % stamp_str
            transactie.save(update_fields=['log'])
            print('[ERROR] Geen token of geen refresh_token')
            # TODO: toon foutmelding pagina en vervolgstappen
        else:
            print('[INFO] Token opgeslagen')

        return HttpResponseRedirect(reverse('Competitie:kies'))


# end of file
