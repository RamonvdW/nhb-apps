# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
from django.db.models import Q
from DataApi.models import DataApiVereniging, DataApiLidmaatschap
from DataApi.view_helpers import datum_n_jaar_geleden, is_auth_token_ok


class VerenigingenView(View):

    @staticmethod
    def _maak_lijst():

        # verenigingen zonder leden moeten we niet rapporteren
        # nadat de vereniging opgeheven is blijven we deze rapporteren,
        # totdat alle DataApiLidmaatschappen die hiernaar verwijzen verwijderd zijn
        ver_nrs_in_use = list(DataApiLidmaatschap.objects.distinct('ver_nr').values_list('ver_nr', flat=True))

        lijst = list()
        for ver in DataApiVereniging.objects.filter(ver_nr__in=ver_nrs_in_use).order_by('pk'):
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
        """ Geeft een lijst met verenigingen terug """

        if not is_auth_token_ok(request):
            return HttpResponseBadRequest('No valid token\n')

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

        # verenigingen zonder leden moeten we niet rapporteren
        # nadat de vereniging opgeheven is blijven we deze rapporteren,
        # totdat alle DataApiLidmaatschappen die hiernaar verwijzen verwijderd zijn
        ver_nrs_in_use = list(DataApiLidmaatschap.objects.distinct('ver_nr').values_list('ver_nr', flat=True))

        lijst = list()
        for ver in DataApiVereniging.objects.filter(ver_nr__in=ver_nrs_in_use).order_by('pk'):
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
        """ Geeft een lijst met verenigingen terug """

        if not is_auth_token_ok(request):
            return HttpResponseBadRequest('No valid token\n')

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
