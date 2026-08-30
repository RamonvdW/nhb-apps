# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from DataApi.models import DataApiVereniging
import datetime


def datum_n_jaar_geleden(jaren: int) -> str:
    now = datetime.datetime.now()

    dagen = jaren * 365
    dagen += jaren // 4     # schrikkeljaren hebben 1 dag meer

    now -= datetime.timedelta(days=dagen)
    return now.strftime('%Y-%m-%d')


class VerenigingenView(View):

    @staticmethod
    def _maak_lijst():

        min_date = datum_n_jaar_geleden(5)
        # print('min_date: %s' % repr(min_date))

        lijst = list()
        for ver in DataApiVereniging.objects.filter(Q(afmeld_datum='') | Q(afmeld_datum__gte=min_date)).order_by('pk'):
            lijst.append({
                "Verenigingscode": str(ver.ver_nr),
                "Naam": ver.naam,
                "Aanmelddatum": ver.aanmeld_datum,
                "Afmelddatum": ver.afmeld_datum,
                "KVKnummer": ver.kvk_nummer,
                "Accommodaties": [
                    {
                        "Postcode": ver.postcode,
                        "Huisnummer": ver.huisnummer,
                    }
                ]
            })
        # for
        return lijst

    def get(self, request, *args, **kwargs):
        """ Geeft een lijst met verenigingen terug

            TODO: Auth token
        """

        # token = request.GET.get('token', '')
        # if token not in settings.KALENDER_API_TOKENS:
        #     token = None

        lijst = self._maak_lijst()

        out = {
            "meta": {
                "count": len(lijst),
                "total": len(lijst),
                "limit": 0,     # len(lijst),
                "offset": 0,
            },
            "Verenigingsgegevens": lijst,
        }

        return JsonResponse(out)


class AccommodatiesView(View):

    @staticmethod
    def _maak_lijst():

        min_date = datum_n_jaar_geleden(5)
        # print('min_date: %s' % repr(min_date))

        lijst = list()
        for ver in DataApiVereniging.objects.filter(Q(afmeld_datum='') | Q(afmeld_datum__gte=min_date)).order_by('pk'):
            lijst.append({
                "Naam": ver.naam,
                "Postcode": ver.postcode,
                "Straat": ver.straatnaam,
                "Huisnummer": ver.huisnummer,
                "Plaats": ver.plaats,
                "Land": ver.land_iso,
                "Longitude": ver.lon,
                "Latitude": ver.lat,
            })
        # for
        return lijst

    def get(self, request, *args, **kwargs):
        """ Geeft een lijst met verenigingen terug

            TODO: Auth token
        """

        # token = request.GET.get('token', '')
        # if token not in settings.KALENDER_API_TOKENS:
        #     token = None

        lijst = self._maak_lijst()

        out = {
            "meta": {
                "count": len(lijst),
                "total": len(lijst),
                "limit": 0,     # len(lijst),
                "offset": 0,
            },
            "Accommodatiegegevens": lijst,
        }

        return JsonResponse(out)


# end of file
