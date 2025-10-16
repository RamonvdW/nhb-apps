# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD, EVENEMENT_STATUS_GEANNULEERD
from Evenement.models import Evenement
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie, EvenementLocatie
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD
from Wedstrijden.models import Wedstrijd
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestKalenderJaar(E2EHelpers, TestCase):

    """ tests voor de Kalender applicatie, module jaaroverzicht """

    url_landing_page = '/kalender/'
    url_kalender_jaar_no_disc = '/kalender/jaar/%s/%s/%s/%s/'               # jaar, maand, soort, bogen
    url_kalender_jaar = '/kalender/jaar/%s/%s/%s/%s/%s/'                    # jaar, maand, soort, bogen, discipline
    url_jaar_simpel = '/kalender/jaar/%s/%s/'                               # jaar, maand
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
        locatie = WedstrijdLocatie(
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

        locatie = EvenementLocatie(
                    naam='Arnhemhal',
                    vereniging=self.ver1,
                    adres='Papendallaan 9\n6816VD Arnhem',
                    plaats='Arnhem')
        locatie.save()

        now_date = timezone.now().date()
        soon_date = now_date + datetime.timedelta(days=10)       # geeft "nog x dagen"

        evenement = Evenement(
                        titel='Test evenement',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=self.ver1,
                        datum=soon_date,
                        aanvang='09:30',
                        inschrijven_tot=1,
                        locatie=locatie,
                        contact_naam='Dhr. Organisator',
                        contact_email='info@test.not',
                        contact_website='www.test.not',
                        contact_telefoon='023-1234567',
                        beschrijving='Test beschrijving',
                        prijs_euro_normaal="15",
                        prijs_euro_onder18="15")
        evenement.save()
        self.evenement = evenement

        datum -= datetime.timedelta(days=1)
        evenement = Evenement(
                        titel='Test evenement 2',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=self.ver1,
                        datum=datum,
                        aanvang='09:30',
                        inschrijven_tot=1,
                        locatie=locatie,
                        contact_naam='Dhr. Organisator',
                        contact_email='info@test.not',
                        contact_website='www.test.not',
                        contact_telefoon='023-1234567',
                        beschrijving='Test beschrijving',
                        prijs_euro_normaal="15",
                        prijs_euro_onder18="15")
        evenement.save()

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

    def test_jaar(self):
        # maand als getal
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar_no_disc % (2020, 1, 'alle', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # illegale maand getallen
        resp = self.client.get(self.url_kalender_jaar % (2020, 0, 'x', 'y', 'alle'))
        self.assert404(resp, 'Geen valide jaar / maand combinatie')
        resp = self.client.post(self.url_kalender_jaar % (2020, 0, 'x', 'y', 'alle'))
        self.assert404(resp, 'Geen valide jaar / maand combinatie')

        # maand als tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 'mrt', 'x', 'y', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # maand als tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 'maart', 'x', 'y', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # illegale maand tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 'xxx', 'x', 'y', 'alle'))
        self.assert404(resp, 'Geen valide maand')

        # illegaal jaar
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2100, 'maart', 'x', 'y', 'alle'))
        self.assert404(resp, 'Geen valide jaar / maand combinatie')

        # wrap-around in december voor 'next'
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 12, 'alle', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))

        # wrap-around in januari voor 'prev'
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 1, 'alle', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        jaar = self.wedstrijd.datum_begin.year
        maand = self.wedstrijd.datum_begin.month

        # soort filters
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (jaar, maand, 'ifaa', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (jaar, maand, 'wa-a', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (jaar, maand, 'wa-b', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (jaar, maand, 'khsn', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (jaar, maand, 'bad', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # discipline filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (jaar, maand, 'bad', 'auto', 'veld'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # zoekterm
        url = self.url_kalender_jaar % (2020, 3, 'bad', 'auto', 'alle')
        url += '?zoek=lowlands'
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # zonder discipline
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_kalender_jaar_no_disc % (2020, 3, 'bad', 'auto'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # log in
        self.e2e_login(self.account_admin)
        self.e2e_wisselnaarrol_sporter()

        # zet een paar voorkeur bogen
        self._zet_boog_voorkeuren(self.sporter)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 'maart', 'alle', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 'maart', 'alle', 'mijn', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 'maart', 'alle', 'bad', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # sporter is geen actief lid
        self.sporter.is_actief_lid = False
        self.sporter.save(update_fields=['is_actief_lid'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (2020, 'maart', 'x', 'mijn', 'alle'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_jaar_simpel % (2020, 'maart'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_verlopen(self):
        # 30 dagen voorbij wedstrijddatum, dan niet meer onder de aandacht brengen
        self.wedstrijd.datum_begin -= datetime.timedelta(days=80)
        self.wedstrijd.datum_einde -= datetime.timedelta(days=80)
        self.wedstrijd.save(update_fields=['datum_begin', 'datum_einde'])
        datum = self.wedstrijd.datum_begin

        # maar 1 wedstrijd over houden
        Wedstrijd.objects.exclude(pk=self.wedstrijd.pk).delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (datum.year, datum.month, 'alle', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.evenement.datum -= datetime.timedelta(days=80)
        self.evenement.status = EVENEMENT_STATUS_GEANNULEERD
        self.evenement.save(update_fields=['datum', 'status'])
        datum = self.evenement.datum

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kalender_jaar % (datum.year, datum.month, 'alle', 'auto', 'alle'))
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp, ('kalender/overzicht-jaar.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

# end of file
