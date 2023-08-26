# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Functie.operations import maak_functie
from Locatie.models import Locatie
from NhbStructuur.models import Regio
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD
from Wedstrijden.models import Wedstrijd
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestKalenderMaand(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie """

    url_landing_page = '/kalender/'
    url_kalender_maand = '/kalender/maand/%s-%s/%s/%s/'                     # maand, jaar, soort, bogen
    url_kalender_pagina = '/kalender/pagina-%s-%s/'                         # jaar, maand
    url_wedstrijden_vereniging = '/wedstrijden/vereniging/'
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_wedstrijd_details = '/wedstrijden/%s/details/'                      # wedstrijd_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        sporter = Sporter(
                    lid_nr=100000,
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    account=self.account_admin)
        sporter.save()
        self.sporter = sporter

        # maak een test vereniging
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        self.ver2 = Vereniging(
                            ver_nr=1001,
                            naam="Kleine Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver2.save()

        # voeg een locatie toe
        locatie = Locatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.ver1)

        datum = timezone.now() + datetime.timedelta(days=30)
        if datum.day >= 29:     # pragma: no cover
            # zorg dat datum+1 dag in dezelfde maand is
            datum += datetime.timedelta(days=7)

        wedstrijd = Wedstrijd(
                        titel='Test 1',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        organiserende_vereniging=self.ver1,
                        locatie=locatie)
        wedstrijd.save()
        self.wedstrijd = wedstrijd

        # geannuleerd
        wedstrijd = Wedstrijd(
                        titel='Test 2',
                        status=WEDSTRIJD_STATUS_GEANNULEERD,
                        datum_begin=datum,
                        datum_einde=datum + datetime.timedelta(days=1),
                        organiserende_vereniging=self.ver1,
                        locatie=locatie)
        wedstrijd.save()

        # langere reeks in dezelfde maand
        wedstrijd = Wedstrijd(
                        titel='Test 3',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum + datetime.timedelta(days=3),
                        organiserende_vereniging=self.ver1,
                        locatie=locatie)
        wedstrijd.save()

        # langere reeks over de maandgrens
        datum = datetime.date(datum.year, datum.month, 28)
        wedstrijd = Wedstrijd(
                        titel='Test 4',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum + datetime.timedelta(days=7),
                        organiserende_vereniging=self.ver1,
                        locatie=locatie)
        wedstrijd.save()

    @staticmethod
    def _zet_boog_voorkeuren(sporter):
        # haal de SporterBoog records op van deze gebruiker
        objs = (SporterBoog
                .objects
                .filter(sporter=sporter)
                .select_related('boogtype')
                .order_by('boogtype__volgorde'))

        # maak ontbrekende SporterBoog records aan, indien nodig
        boogtypen = BoogType.objects.exclude(buiten_gebruik=True)
        if len(objs) < len(boogtypen):                                 # pragma: no branch
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            bulk = list()
            for boogtype in boogtypen.exclude(pk__in=aanwezig):
                sporterboog = SporterBoog(
                                    sporter=sporter,
                                    boogtype=boogtype)
                bulk.append(sporterboog)
            # for
            SporterBoog.objects.bulk_create(bulk)

    def test_maand(self):
        # maand als getal
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (1, 2020, 'alle', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # illegale maand getallen
        resp = self.client.get(self.url_kalender_maand % (0, 2020, 'x', 'y'))
        self.assert404(resp, 'Geen valide jaar / maand combinatie')
        resp = self.client.post(self.url_kalender_maand % (0, 2020, 'x', 'y'))
        self.assert404(resp, 'Geen valide jaar / maand combinatie')

        # maand als tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % ('mrt', 2020, 'x', 'y'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # maand als tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % ('maart', 2020, 'x', 'y'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # illegale maand tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % ('xxx', 2020, 'x', 'y'))
        self.assert404(resp, 'Geen valide maand')

        # illegaal jaar
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % ('maart', 2100, 'x', 'y'))
        self.assert404(resp, 'Geen valide jaar / maand combinatie')

        # wrap-around in december voor 'next'
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (12, 2020, 'alle', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))

        # wrap-around in januari voor 'prev'
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (1, 2020, 'alle', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # soort filters
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (3, 2020, 'ifaa', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (3, 2020, 'wa-a', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (3, 2020, 'wa-b', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (3, 2020, 'khsn', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % (3, 2020, 'bad', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # zoekterm
        url = self.url_kalender_maand % (3, 2020, 'bad', 'auto')
        url += '?zoek=lowlands'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # log in
        self.e2e_login(self.account_admin)
        self.e2e_wisselnaarrol_sporter()

        # zet een paar voorkeur bogen
        self._zet_boog_voorkeuren(self.sporter)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % ('maart', 2020, 'alle', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % ('maart', 2020, 'alle', 'mijn'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % ('maart', 2020, 'alle', 'bad'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # sporter is geen actief lid
        self.sporter.is_actief_lid = False
        self.sporter.save(update_fields=['is_actief_lid'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_maand % ('maart', 2020, 'x', 'mijn'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_landing(self):
        self.client.logout()

        # haal de maand pagina op met een wedstrijd erop
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_landing_page)
        self.assertEqual(resp.status_code, 302)     # redirect naar juiste maand-pagina
        url = resp.url

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))

        # log in, zodat het mandje eval gedaan wordt
        self.e2e_login(self.account_admin)
        self.e2e_wisselnaarrol_sporter()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_legacy(self):
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_pagina % (2020, 'maart'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-maand.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

# end of file
