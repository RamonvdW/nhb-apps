# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Bestel.definities import BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF
from Bestel.models import Bestelling, BestelProduct
from Betaal.models import BetaalInstellingenVereniging
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD
from Evenement.models import Evenement, EvenementSessie, EvenementInschrijving
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestEvenementInschrijven(E2EHelpers, TestCase):

    """ tests voor de Evenement applicatie, module Inschrijven """

    test_after = ('Bestel.tests.test_mandje',)

    url_details = '/kalender/evenement/details/%s/'                              # evenement_pk
    url_inschrijven_sporter = '/kalender/evenement/inschrijven/%s/sporter/'      # evenement_pk
    url_toevoegen_mandje = '/kalender/evenement/inschrijven/toevoegen-mandje/'   # POST

    volgende_bestel_nr = 1234567

    def setUp(self):
        """ initialisatie van de test case """

        # self.account_admin = account = self.e2e_create_account_admin()
        # self.account_admin.is_BB = True
        # self.account_admin.save(update_fields=['is_BB'])

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Tester')

        ver_bond = Vereniging(
                    ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                    naam='Bondsbureau',
                    plaats='Schietstad',
                    regio=Regio.objects.get(regio_nr=100))
        ver_bond.save()
        self.ver_bond = ver_bond

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver_bond,
                            mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen_bond = instellingen

        self.assertEqual(settings.BETAAL_VIA_BOND_VER_NR, settings.WEBWINKEL_VERKOPER_VER_NR)

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
        ver.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_bond=True)
        instellingen.save()
        self.instellingen = instellingen

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.account_100000,
                        bij_vereniging=ver)
        sporter.save()
        self.sporter = sporter

        locatie = EvenementLocatie(
                    naam='Arnhemhal',
                    vereniging=ver,
                    adres='Papendallaan 9\n6816VD Arnhem',
                    plaats='Arnhem')
        locatie.save()

        now_date = timezone.now().date()
        soon_date = now_date + datetime.timedelta(days=60)

        evenement = Evenement(
                        titel='Test evenement',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=ver,
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

    def test_anon(self):
        resp = self.client.get(self.url_details % self.evenement.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/details.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_details % 999999)
        self.assert404(resp, "Evenement niet gevonden")

        resp = self.client.get(self.url_inschrijven_sporter % 99999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.post(self.url_toevoegen_mandje)
        self.assert403(resp, "Geen toegang")

    def test_details(self):
        self.e2e_login(self.account_100000)

        url = self.url_details % self.evenement.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/details.dtl', 'plein/site_layout.dtl'))

        # zet datum in het verleden
        self.evenement.datum = timezone.now().date()       # 1 dag ervoor
        self.evenement.save(update_fields=['datum'])

        self.assertTrue(str(self.evenement) != '')

        # kan niet meer inschrijven
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/details.dtl', 'plein/site_layout.dtl'))

    def test_sporter(self):
        # inlog vereist
        self.e2e_login(self.account_100000)

        resp = self.client.get(self.url_inschrijven_sporter % 99999)
        self.assert404(resp, "Evenement niet gevonden")

        url = self.url_inschrijven_sporter % self.evenement.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.assertEqual(EvenementInschrijving.objects.count(), 0)

        # echte inschrijving
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                                'sporter': self.sporter.pk,
                                                                'goto': 'S',
                                                                'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(EvenementInschrijving.objects.count(), 1)

        #f1, f2 = self.verwerk_bestel_mutaties()
        # print('f1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        #self.assertTrue(": inschrijven op evenement" in f2.getvalue())

        self.assertEqual(EvenementInschrijving.objects.count(), 1)
        inschrijving = EvenementInschrijving.objects.first()
        self.assertEqual(inschrijving.evenement, self.evenement)
        self.assertEqual(inschrijving.sporter, self.sporter)

        # al ingeschreven
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # uitzonderingen
        self.account_100000.username = 'normaal'
        self.account_100000.save(update_fields=['username'])
        resp = self.client.get(url)
        self.assert404(resp, "Bondsnummer ontbreekt")

        self.account_100000.username = '999999'
        self.account_100000.save(update_fields=['username'])
        resp = self.client.get(url)

        # zet datum in het verleden
        self.evenement.datum = timezone.now().date()       # 1 dag ervoor
        self.evenement.save(update_fields=['datum'])

        resp = self.client.get(url)
        self.assert404(resp, "Inschrijving is gesloten")

    def test_toevoegen_aan_mandje(self):
        # inlog vereist
        self.e2e_login(self.account_100000)

        # inschrijven
        resp = self.client.post(self.url_toevoegen_mandje)
        self.assert404(resp, "Slecht verzoek")

        resp = self.client.post(self.url_toevoegen_mandje, {'evenement': 9999999,
                                                            'sporter': 'xx'})
        self.assert404(resp, "Slecht verzoek")

        resp = self.client.post(self.url_toevoegen_mandje, {'evenement': 9999999,
                                                            'sporter': 9999999})
        self.assert404(resp, "Onderdeel van verzoek niet gevonden")

        resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                            'sporter': 9999999})
        self.assert404(resp, "Onderdeel van verzoek niet gevonden")

        # evenement is in het verleden
        self.evenement.datum -= datetime.timedelta(days=500)
        self.evenement.save(update_fields=['datum'])

        resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                            'sporter': self.sporter.pk})
        self.assert404(resp, "Inschrijving is gesloten")

        self.evenement.datum += datetime.timedelta(days=500)
        self.evenement.save(update_fields=['datum'])

        # sporter is geen actief lid
        self.sporter.is_actief_lid = False
        self.sporter.save(update_fields=['is_actief_lid'])

        resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                            'sporter': self.sporter.pk})
        self.assert404(resp, "Niet actief lid")

        self.sporter.is_actief_lid = True
        self.sporter.save(update_fields=['is_actief_lid'])

        # echte inschrijving
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                                'sporter': self.sporter.pk,
                                                                'goto': 'F',
                                                                'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)


# end of file
