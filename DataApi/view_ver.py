# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import JsonResponse, HttpResponse
from django.views import View
from django.db.models import Q
from DataApi.models import DataApiVereniging, DataApiLidmaatschap
from DataApi.view_helpers import datum_n_jaar_geleden, is_auth_token_ok
from Logboek.operations import schrijf_in_logboek


def _get_ver_nrs_in_use():
    # verenigingen zonder leden moeten we niet rapporteren
    # nadat de vereniging opgeheven is blijven we deze rapporteren,
    # totdat alle DataApiLidmaatschappen die hiernaar verwijzen verwijderd zijn

    # rapporteren maximaal 5 jaar aan lidmaatschappen
    actief_datum = datum_n_jaar_geleden(5)

    ver_nrs = list(DataApiLidmaatschap
                   .objects
                   .filter(Q(afmeld_datum='') | Q(afmeld_datum__gte=actief_datum))
                   .distinct('ver_nr')
                   .values_list('ver_nr', flat=True))
    return ver_nrs


class VerenigingenView(View):

    @staticmethod
    def _maak_lijst():

        ver_nrs_in_use = _get_ver_nrs_in_use()

        lijst = list()
        for ver in (DataApiVereniging
                    .objects
                    .filter(ver_nr__in=ver_nrs_in_use)
                    .order_by('pk')):

            lijst.append(
                {
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
                }
            )
        # for

        return lijst

    def get(self, request, *args, **kwargs):
        """ Geeft een lijst met verenigingen terug """

        if not is_auth_token_ok(request):
            return HttpResponse('No valid token\n', status=401)

        lijst = self._maak_lijst()

        meta = {
            "count": len(lijst),
            "total": len(lijst),
        }

        out = {
            "meta": meta,
            "Verenigingsgegevens": lijst,
        }

        schrijf_in_logboek(
                None,    # systeem
                'Data API',
                'Verenigingen worden opgehaald. Meta: %s' % repr(meta))

        return JsonResponse(out)


class AccommodatiesView(View):

    @staticmethod
    def _maak_lijst():

        ver_nrs_in_use = _get_ver_nrs_in_use()

        lijst = list()
        for ver in (DataApiVereniging
                    .objects
                    .filter(ver_nr__in=ver_nrs_in_use)
                    .order_by('pk')):

            lijst.append(
                {
                    "Naam": ver.naam,
                    "Postcode": ver.postcode,
                    "Straat": ver.straatnaam,
                    "Huisnummer": ver.huisnummer,
                    "Plaats": ver.plaats,
                    "Land": ver.land_iso,
                    "Longitude": ver.lon,
                    "Latitude": ver.lat,
                }
            )
        # for

        return lijst

    def get(self, request, *args, **kwargs):
        """ Geeft een lijst met verenigingen terug """

        if not is_auth_token_ok(request):
            return HttpResponse('No valid token\n', status=401)

        lijst = self._maak_lijst()

        meta = {
            "count": len(lijst),
            "total": len(lijst),
        }

        out = {
            "meta": meta,
            "Accommodatiegegevens": lijst,
        }

        schrijf_in_logboek(
                None,    # systeem
                'Data API',
                'Accommodaties worden opgehaald. Meta: %s' % repr(meta))

        return JsonResponse(out)


class BestaatNiet(View):

    def dispatch(self, request, *args, **kwargs):
        return HttpResponse('No such endpoint\n', status=400)


# end of file
