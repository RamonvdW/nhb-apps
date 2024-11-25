# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.decorators.cache import cache_control
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD, EVENEMENT_STATUS_GEANNULEERD
from Evenement.models import Evenement
from Kalender.view_maand import maak_compacte_wanneer_str
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD
from Wedstrijden.models import Wedstrijd
import datetime
import time


class ApiView(View):

    @staticmethod
    @cache_control(max_age=3600)        # 1 hour
    def get(request, *args, **kwargs):
        """ Geeft een lijst met evenementen/wedstrijden/opleidingen terug

            aantal_maanden_vooruit: 1..36 maanden

            verplichte parameter: token
        """

        token = request.GET.get('token', '')
        if token not in settings.KALENDER_API_TOKENS:
            token = None

        try:
            dagen = int(kwargs['aantal_dagen_vooruit'])
        except (KeyError, ValueError, TypeError):
            dagen = 1

        dagen = max(1, dagen)           # at least 1
        dagen = min(3*365, dagen)       # at most 3 years

        datum_vanaf = timezone.now().date()
        datum_voor = datum_vanaf + datetime.timedelta(days=dagen)

        out = dict()
        out['lijst'] = lijst = list()

        # geef alleen een antwoord als een valide token opgegeven is
        if token:
            wedstrijden = (Wedstrijd
                           .objects
                           .select_related('locatie')
                           .exclude(toon_op_kalender=False)
                           .exclude(locatie=None)
                           .filter(datum_begin__gte=datum_vanaf,
                                   datum_begin__lt=datum_voor,
                                   status__in=(WEDSTRIJD_STATUS_GEACCEPTEERD,
                                               WEDSTRIJD_STATUS_GEANNULEERD)))

            for wedstrijd in wedstrijden:
                url = reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk})
                url = settings.SITE_URL + url
                datums_str = maak_compacte_wanneer_str(wedstrijd.datum_begin, wedstrijd.datum_einde)
                lijst.append({
                    'sort': wedstrijd.datum_begin.strftime('%Y%m%d') + 'W' + wedstrijd.locatie.plaats + wedstrijd.titel,
                    'datum': datums_str,
                    'plaats': wedstrijd.locatie.plaats,
                    'titel': wedstrijd.titel,
                    'link': url,
                    'geannuleerd': wedstrijd.status == WEDSTRIJD_STATUS_GEANNULEERD,
                })
            # for

        if token:
            evenementen = (Evenement
                           .objects
                           .select_related('locatie')
                           .exclude(locatie=None)
                           .filter(datum__gte=datum_vanaf,
                                   datum__lt=datum_voor,
                                   status__in=(EVENEMENT_STATUS_GEACCEPTEERD,
                                               EVENEMENT_STATUS_GEANNULEERD)))

            for evenement in evenementen:
                url = reverse('Evenement:details', kwargs={'evenement_pk': evenement.pk})
                url = settings.SITE_URL + url
                datums_str = maak_compacte_wanneer_str(evenement.datum_begin, evenement.datum_einde)
                lijst.append({
                    'sort': evenement.datum_begin.strftime('%Y%m%d') + 'E' + evenement.locatie.plaats + evenement.titel,
                    'datum': datums_str,
                    'plaats': evenement.locatie.plaats,
                    'titel': evenement.titel,
                    'link': url,
                    'geannuleerd': evenement.status == EVENEMENT_STATUS_GEANNULEERD,
                })
            # for

        if token:
            lijst.sort(key=lambda d: d['sort'])        # sorteer op datum
            for obj in lijst:
                del obj['sort']
            # for

        if not token:
            time.sleep(1)     # speed limiter

        return JsonResponse(out)


# end of file
