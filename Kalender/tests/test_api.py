# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from Geo.models import Regio
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD
from Evenement.models import Evenement
from Locatie.models import WedstrijdLocatie, EvenementLocatie
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD
from Wedstrijden.models import Wedstrijd
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestKalenderAPI(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie, API module """

    url_kalender_api = '/kalender/api/lijst/%s/'       # dagen vooruit

    def setUp(self):
        """ initialisatie van de test case """

        # maak een test vereniging
        ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        ver1.save()

        ver2 = Vereniging(
                            ver_nr=1001,
                            naam="Kleine Club",
                            regio=Regio.objects.get(regio_nr=112))
        ver2.save()

        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(ver1)

        datum = timezone.now() + datetime.timedelta(days=30)
        if datum.day >= 29:     # pragma: no cover
            # zorg dat datum+1 dag in dezelfde maand is
            datum += datetime.timedelta(days=7)

        wedstrijd = Wedstrijd(
                        titel='Test 1',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        organiserende_vereniging=ver1,
                        locatie=locatie)
        wedstrijd.save()

        # geannuleerd
        wedstrijd = Wedstrijd(
                        titel='Test 2',
                        status=WEDSTRIJD_STATUS_GEANNULEERD,
                        datum_begin=datum,
                        datum_einde=datum + datetime.timedelta(days=1),
                        organiserende_vereniging=ver1,
                        locatie=locatie)
        wedstrijd.save()

        # langere reeks in dezelfde maand
        wedstrijd = Wedstrijd(
                        titel='Test 3',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum + datetime.timedelta(days=3),
                        organiserende_vereniging=ver1,
                        locatie=locatie)
        wedstrijd.save()

        # langere reeks over de maandgrens
        datum = datetime.date(datum.year, datum.month, 28)
        wedstrijd = Wedstrijd(
                        titel='Test 4',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum + datetime.timedelta(days=7),
                        organiserende_vereniging=ver1,
                        locatie=locatie)
        wedstrijd.save()

        # in het verleden
        datum2 = datum - datetime.timedelta(days=60)
        wedstrijd = Wedstrijd(
                        titel='Test 5',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum2,
                        datum_einde=datum2,
                        organiserende_vereniging=ver1,
                        locatie=locatie)
        wedstrijd.save()

        locatie = EvenementLocatie(
                        naam='Test',
                        vereniging=ver2,
                        adres='Test')
        locatie.save()

        evenement = Evenement(
                        titel='Test',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=ver2,
                        datum=datum,
                        locatie=locatie)
        evenement.save()

    def test_api(self):
        # no token
        dagen_vooruit = 1
        url = self.url_kalender_api % dagen_vooruit
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        json_data = self.assert200_json(resp)
        self.assertEqual(len(json_data.keys()), 0)

        # correctie request
        dagen_vooruit = 60
        url = self.url_kalender_api % dagen_vooruit
        url += '?token=' + settings.KALENDER_API_TOKENS[0]
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        json_data = self.assert200_json(resp)
        self.assertTrue("lijst" in json_data)
        # TODO: data beter checken

        # bad aantal dagen
        # moet integer zijn. Bij fout: valt terug op 0 dagen
        url = self.url_kalender_api % "bad"
        url += '?token=' + settings.KALENDER_API_TOKENS[0]
        resp = self.client.get(url)
        json_data = self.assert200_json(resp)
        self.assertTrue("lijst" in json_data)

# end of file
