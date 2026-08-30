# -*- coding: utf-8 -*-
import django.http.response
#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import JsonResponse, Http404, HttpResponseBadRequest
from django.views import View
from DataApi.models import DataApiLidmaatschap
import datetime
import hashlib


def datum_n_jaar_geleden(jaren: int) -> str:
    now = datetime.datetime.now()

    dagen = jaren * 365
    dagen += jaren // 4     # schrikkeljaren hebben 1 dag meer

    now -= datetime.timedelta(days=dagen)
    return now.strftime('%Y-%m-%d')


class LidmaatschappenView(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._limit = 0
        self._offset = 0
        self._peildatum = datum_n_jaar_geleden(5)

    def _maak_lidmaatschapid(self, lms: DataApiLidmaatschap) -> str:
        # maak een unieke code die stabiel is
        # gebruik: lid_nr, geboortedatum, geslacht, postcode, land, ver_nr, aanmelddatum
        calc = hashlib.sha1()
        data = "v1 %s %s %s %10s %s %s %s" % (lms.lid_nr, lms.geboorte_datum, lms.geslacht, lms.postcode,
                                              lms.land_iso, lms.ver_nr, lms.aanmeld_datum)
        calc.update(data.encode())
        digest = calc.hexdigest()
        return digest

    def _maak_lijst(self):
        lijst = list()

        qset = DataApiLidmaatschap.objects.all()
        if self._peildatum:
            qset = qset.filter(mutatie_datum__gte=self._peildatum)
        total = qset.count()

        start_nr = self._offset
        if self._limit > 0:
            stop_nr = self._offset + self._limit
        else:
            stop_nr = self._offset + 10

        for lms in qset.order_by('pk')[start_nr:stop_nr]:
            ver_code = str(lms.ver_nr) if lms.ver_nr > 0 else ''

            lijst.append({
                "LidmaatschapsID": self._maak_lidmaatschapid(lms),
                "Lidcode": str(lms.lid_nr),
                "Verenigingscode": ver_code,
                "Postcode": lms.postcode,
                "Land": lms.land_iso,
                "Geboortedatum": lms.geboorte_datum,
                "Geslacht": lms.geslacht.lower(),
                "Aanmelddatum": lms.aanmeld_datum,
                "Afmelddatum": lms.afmeld_datum,
                "Sporttak": [
                    "handboogsport",
                ]
            })
        # for

        return lijst, total

    def _get_params(self, request):
        """
            Reageer op query parameters
            raised een ValueError als er iets fout is met deze parameters
        """
        peildatum = request.GET.get('peildatum', '')[:20]   # afkappen voor de veiligheid
        if peildatum:
            if len(peildatum) != 10:
                raise ValueError('Geen valide peildatum lengte')
            if peildatum[4] != '-' or peildatum[7] != '-':
                raise ValueError('Geen valide peildatum (YMD)')
            if peildatum[:2] != '20':
                raise ValueError('Geen valide peildatum eeuw')
            try:
                datum_p = datetime.datetime.strptime(peildatum, '%Y-%m-%d')
            except (ValueError, TypeError, IndexError):
                raise ValueError('Geen valide peildatum (inhoudelijk)')
            self._peildatum = datum_p.strftime('%Y-%m-%d')

        limit = request.GET.get('limit', '')[:6]    # afkappen voor de veiligheid
        if limit:
            try:
                n = int(limit)
            except (ValueError, TypeError, IndexError) as exc:
                raise ValueError('Geen valide limit (getal)')

            if 0 < n <= 5000:
                self._limit = n
            else:
                raise ValueError('Geen valide limit (range)')

        offset = request.GET.get('offset', '')[:6]    # afkappen voor de veiligheid
        if offset:
            try:
                n = int(offset)
            except (ValueError, TypeError, IndexError):
                raise ValueError('Geen valide offset (getal)')
            if 0 <= n < 100000:
                self._offset = n
            else:
                raise ValueError('Geen valide offset (range)')

    def get(self, request, *args, **kwargs):
        """ Geeft een lijst met verenigingen terug

            TODO: Auth token
        """

        # token = request.GET.get('token', '')
        # if token not in settings.KALENDER_API_TOKENS:
        #     token = None

        try:
            self._get_params(request)
        except ValueError as exc:
            # geef antwoord met een status 400
            return HttpResponseBadRequest("%s\n" % exc)

        lijst, total = self._maak_lijst()

        out = {
            "meta": {
                "count": len(lijst),
                "total": total,
                "limit": self._limit,
                "offset": self._offset,
            },
            "Lidmaatschapsgegevens": lijst,
        }

        return JsonResponse(out)


# end of file
