# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Betaal.models import BetaalInstellingenVereniging
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD
from Evenement.models import Evenement, EvenementInschrijving
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestEvenementInschrijven(E2EHelpers, TestCase):

    """ tests voor de Evenement applicatie, module Inschrijven """

    test_after = ('Bestel.tests.test_mandje', 'Evenement.tests.test_details')

    url_inschrijven_sporter = '/kalender/evenement/inschrijven/%s/sporter/'         # evenement_pk
    url_inschrijven_groepje = '/kalender/evenement/inschrijven/%s/groep/'           # evenement_pk
    url_inschrijven_familie = '/kalender/evenement/inschrijven/%s/familie/'         # evenement_pk
    url_inschrijven_familie_lid = '/kalender/evenement/inschrijven/%s/familie/%s/'  # evenement_pk, lid_nr
    url_toevoegen_mandje = '/kalender/evenement/inschrijven/toevoegen-mandje/'      # POST

    volgende_bestel_nr = 1234567

    def setUp(self):
        """ initialisatie van de test case """

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Tester')
        self.account_100022 = self.e2e_create_account('100022', 'pijl@test.not', 'Pijl')

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
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        self.sporter_100000 = sporter

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

        # nog een sporter met account (voor inschrijven groepje)
        sporter = Sporter(
                        lid_nr=100022,
                        voornaam='Pijl',
                        achternaam='de Boog',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.account_100022,
                        bij_vereniging=ver,
                        adres_code='5678YY')
        sporter.save()
        self.sporter_100022 = sporter

        # nog een sporter, zonder account
        sporter = Sporter(
                        lid_nr=100023,
                        voornaam='Pees',
                        achternaam='de Boog',
                        geboorte_datum='1966-05-05',
                        sinds_datum='2020-02-02',
                        bij_vereniging=ver)
        sporter.save()
        self.sporter_100023 = sporter

    def test_anon(self):
        resp = self.client.get(self.url_inschrijven_sporter % 99999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_inschrijven_groepje % 99999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.post(self.url_toevoegen_mandje)
        self.assert403(resp, "Geen toegang")

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
                                                                'sporter': self.sporter_100000.pk,
                                                                'goto': 'S',
                                                                'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(EvenementInschrijving.objects.count(), 1)

        # f1, f2 = self.verwerk_bestel_mutaties()
        # print('f1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        # self.assertTrue(": inschrijven op evenement" in f2.getvalue())

        self.assertEqual(EvenementInschrijving.objects.count(), 1)
        inschrijving = EvenementInschrijving.objects.first()
        self.assertEqual(inschrijving.evenement, self.evenement)
        self.assertEqual(inschrijving.sporter, self.sporter_100000)

        # coverage
        self.assertTrue(str(inschrijving) != '')
        self.assertEqual(inschrijving.korte_beschrijving(), 'Test evenement, voor 100000')
        inschrijving.evenement.titel = 'Dit is een hele lange titel die afgekapt gaat worden'
        self.assertTrue('.., voor 100000' in inschrijving.korte_beschrijving())

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
        # TODO: check resp

        # zet datum in het verleden
        self.evenement.datum = timezone.now().date()       # 1 dag ervoor
        self.evenement.save(update_fields=['datum'])

        resp = self.client.get(url)
        self.assert404(resp, "Inschrijving is gesloten")

    def test_groepje(self):
        # inlog vereist
        self.e2e_login(self.account_100000)

        resp = self.client.get(self.url_inschrijven_groepje % 99999)
        self.assert404(resp, "Evenement niet gevonden")

        url = self.url_inschrijven_groepje % self.evenement.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # niet gevonden
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'bondsnummer': 999999})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Sporter 999999 niet gevonden.')

        # geen valide bondsnummer
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'bondsnummer': 42})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'Sporter 42 niet gevonden.')

        # wel gevonden
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'bondsnummer': 100022})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'Sporter 100022 niet gevonden.')

        # wel gevonden, maar geen account
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'bondsnummer': 100023})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.assertEqual(EvenementInschrijving.objects.count(), 0)

        # echte inschrijving
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                                'sporter': self.sporter_100022.pk,
                                                                'goto': 'G',
                                                                'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(EvenementInschrijving.objects.count(), 1)

        # f1, f2 = self.verwerk_bestel_mutaties()
        # print('f1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        # self.assertTrue(": inschrijven op evenement" in f2.getvalue())

        self.assertEqual(EvenementInschrijving.objects.count(), 1)
        inschrijving = EvenementInschrijving.objects.first()
        self.assertEqual(inschrijving.evenement, self.evenement)
        self.assertEqual(inschrijving.sporter, self.sporter_100022)

        # wel gevonden, al ingeschreven
        with self.assert_max_queries(20):
            resp = self.client.get(url, {'bondsnummer': 100022})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        # self.e2e_open_in_browser(resp)
        self.assertContains(resp, 'Al ingeschreven')

    def test_familie(self):
        # inlog vereist
        self.e2e_login(self.account_100000)

        resp = self.client.get(self.url_inschrijven_familie % 99999)
        self.assert404(resp, "Evenement niet gevonden")

        resp = self.client.get(self.url_inschrijven_familie_lid % (self.evenement.pk, self.sporter_100022.lid_nr))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-familie.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, '[100022]')
        self.assertNotContains(resp, '[100023]')

        self.sporter_100022.adres_code = self.sporter_100000.adres_code
        self.sporter_100022.save(update_fields=['adres_code'])
        resp = self.client.get(self.url_inschrijven_familie_lid % (self.evenement.pk, self.sporter_100022.lid_nr))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-familie.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, '[100022]')
        self.assertNotContains(resp, '[100023]')

        # bad urls
        resp = self.client.get(self.url_inschrijven_familie_lid % (self.evenement.pk, 'x'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid % (self.evenement.pk, '0.5'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_inschrijven_familie_lid % (self.evenement.pk, '42'))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-familie.dtl', 'plein/site_layout.dtl'))

    def test_gast(self):
        self.sporter_100000.is_gast = True
        self.sporter_100000.save(update_fields=['is_gast'])

        self.account_100000.is_gast = True
        self.account_100000.save(update_fields=['is_gast'])

        # inlog vereist
        self.e2e_login(self.account_100000)

        resp = self.client.get(self.url_inschrijven_sporter % self.evenement.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-sporter.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Het is niet mogelijk om in te schrijven op dit evenement')

        resp = self.client.get(self.url_inschrijven_groepje % self.evenement.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-groepje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertNotContains(resp, 'Het is niet mogelijk om in te schrijven op dit evenement')

        resp = self.client.get(self.url_inschrijven_familie % self.evenement.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-familie.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'Het is niet mogelijk om in te schrijven op dit evenement')

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
                                                            'sporter': self.sporter_100000.pk})
        self.assert404(resp, "Inschrijving is gesloten")

        self.evenement.datum += datetime.timedelta(days=500)
        self.evenement.save(update_fields=['datum'])

        # sporter is geen actief lid
        self.sporter_100000.is_actief_lid = False
        self.sporter_100000.save(update_fields=['is_actief_lid'])

        resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                            'sporter': self.sporter_100000.pk})
        self.assert404(resp, "Niet actief lid")

        self.sporter_100000.is_actief_lid = True
        self.sporter_100000.save(update_fields=['is_actief_lid'])

        # echte inschrijving
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                                'sporter': self.sporter_100000.pk,
                                                                'goto': 'F',
                                                                'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)


# end of file
