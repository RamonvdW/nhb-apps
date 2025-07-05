# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD, EVENEMENT_STATUS_GEANNULEERD
from Evenement.models import Evenement
from Kalender.view_zoek import maak_compacte_wanneer_str
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD,
                                    WEDSTRIJD_DISCIPLINE_TO_STR_KHSN)
from Wedstrijden.models import Wedstrijd
from collections import OrderedDict
import datetime


class ApiView(View):

    @staticmethod
    def _maak_lijst(datum_vanaf, datum_voor):
        lijst = list()

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
                'discipline': WEDSTRIJD_DISCIPLINE_TO_STR_KHSN[wedstrijd.discipline],
            })
        # for

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
            datums_str = maak_compacte_wanneer_str(evenement.datum, evenement.datum)
            lijst.append({
                'sort': evenement.datum.strftime('%Y%m%d') + 'E' + evenement.locatie.plaats + evenement.titel,
                'datum': datums_str,
                'plaats': evenement.locatie.plaats,
                'titel': evenement.titel,
                'link': url,
                'geannuleerd': evenement.status == EVENEMENT_STATUS_GEANNULEERD,
                'discipline': 'Evenement',
            })
        # for

        lijst.sort(key=lambda d: d['sort'])        # sorteer op datum
        for obj in lijst:
            del obj['sort']
        # for

        return lijst

    @staticmethod
    def _maak_discipline_geschiedenis(discipline) -> list:
        """ geef de 5 laatste wedstrijden van deze discipline """

        lijst = list()
        datum_voor = timezone.now()

        wedstrijden = (Wedstrijd
                       .objects
                       .select_related('locatie')
                       .exclude(toon_op_kalender=False)
                       .exclude(locatie=None)
                       .filter(datum_begin__lt=datum_voor,
                               discipline=discipline,
                               status=WEDSTRIJD_STATUS_GEACCEPTEERD)
                       .order_by('-datum_begin',              # nieuwste eerst
                                 'locatie__plaats'))[:5]

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
            })
        # for

        lijst.sort(key=lambda d: d['sort'], reverse=True)        # sorteer op datum, oudste eerst
        for obj in lijst:
            del obj['sort']
        # for

        return lijst

    def get(self, request, *args, **kwargs):
        """ Geeft een lijst met evenementen/wedstrijden/opleidingen terug

            # aantal_dagen_terug: 1..1000 dagen
            aantal_dagen_vooruit: 1..36 dagen

            verplichte parameter: token
        """

        token = request.GET.get('token', '')
        if token not in settings.KALENDER_API_TOKENS:
            token = None

        try:
            dagen_plus = int(kwargs['aantal_dagen_vooruit'])
        except (KeyError, ValueError, TypeError):
            dagen_plus = 0

        dagen_plus = max(0, dagen_plus)           # at least 0
        dagen_plus = min(5*365, dagen_plus)       # at most 5 years

        datum_vanaf = timezone.now().date()
        datum_voor = datum_vanaf + datetime.timedelta(days=dagen_plus)
        # print('range: %s .. %s' % (datum_vanaf, datum_voor))

        out = dict()

        # geef alleen een antwoord als een valide token opgegeven is
        if token:
            out['lijst'] = self._maak_lijst(datum_vanaf, datum_voor)

            out['eerdere_wedstrijden'] = disciplines = OrderedDict()
            codes = list(WEDSTRIJD_DISCIPLINE_TO_STR_KHSN.keys())
            codes.sort()
            for code in codes:
                discipline_naam = WEDSTRIJD_DISCIPLINE_TO_STR_KHSN[code]
                disciplines[discipline_naam] = self._maak_discipline_geschiedenis(code)
            # for

        return JsonResponse(out)


# end of file
