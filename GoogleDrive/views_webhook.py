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

        # get the query parameters
        state = request.GET.get('state', None)
        if not state:
            raise Http404('Slecht verzoek')

        code = request.GET.get('code', None)        # authorization code with typical lifetime of 10 minutes
        error = request.GET.get('error', None)

        # security: filter onvolledige aanroepen, zonder database query
        if not (error or code):
            raise Http404('Onvolledig verzoek')

        # kijk in de database of we dit verzoek herkennen
        age_filter = timezone.now() - timedelta(hours=1)
        try:
            transactie = (Transactie
                          .objects
                          .exclude(has_been_used=True)
                          .exclude(when__lt=age_filter)
                          .filter(unieke_code=state)
                          .first())
        except Transactie.DoesNotExist:
            transactie = None

        if not transactie:
            raise Http404('Onbekend verzoek')

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        uri = request.get_full_path()

        # noteer de ontvangst in het logboek en blokkeer verdere doorgang via deze webhook
        transactie.has_been_used = True
        transactie.log += "[%s] Webhook aanroep: %s\n" % (stamp_str, uri)
        transactie.save(update_fields=['log', 'has_been_used'])

        token = handle_authentication_response(uri)
        if not token:
            # voeg een foutmelding toe aan het logboek van de transactie
            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            transactie.log += "[%s] Geen bruikbaar token of geen refresh token)\n" % stamp_str
            transactie.save(update_fields=['log'])

            next_url = reverse('GoogleDrive:resultaat-mislukt')
        else:
            # success: bruikbaar token ontvangen
            next_url = reverse('GoogleDrive:resultaat-gelukt')

        return HttpResponseRedirect(next_url)


# end of file
