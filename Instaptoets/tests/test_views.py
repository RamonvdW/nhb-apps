# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Geo.models import Regio
from Instaptoets.models import Categorie, Instaptoets, Vraag
from Instaptoets.operations import selecteer_huidige_vraag
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


def toets_zet_afgerond_niet_geslaagd(toets):
    toets.aantal_antwoorden = toets.aantal_vragen
    toets.is_afgerond = True
    toets.geslaagd = False
    toets.save(update_fields=['is_afgerond', 'aantal_antwoorden', 'geslaagd'])


def toets_zet_geslaagd_nog_geldig(toets):
    toets.aantal_antwoorden = toets.aantal_vragen
    toets.is_afgerond = True
    toets.geslaagd = True
    toets.afgerond = timezone.now()
    toets.save(update_fields=['is_afgerond', 'aantal_antwoorden', 'geslaagd', 'afgerond'])


def toets_zet_geslaagd_niet_meer_geldig(toets):
    toets.aantal_antwoorden = toets.aantal_vragen
    toets.is_afgerond = True
    toets.geslaagd = True
    toets.afgerond = timezone.now() - datetime.timedelta(days=400)
    toets.save(update_fields=['is_afgerond', 'aantal_antwoorden', 'geslaagd', 'afgerond'])


class TestInstaptoetsViews(E2EHelpers, TestCase):

    """ tests voor de Instaptoets applicatie, module view_toets """

    test_after = ('Sporter.tests.test_login',)

    url_begin = '/opleiding/instaptoets/'
    url_uitslag = url_begin + 'uitslag/'
    url_volgende_vraag = url_begin + 'volgende-vraag/'
    url_ontvang_antwoord = url_begin + 'vraag-antwoord/'
    url_opleiding_overzicht = '/opleiding/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Normaal')

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

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Jan',
                        achternaam='van de Toets',
                        geboorte_datum='1977-07-07',
                        sinds_datum='2024-02-02',
                        account=self.account_100000,
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        self.sporter_100000 = sporter

        self._maak_vragen()

    @staticmethod
    def _maak_vragen():
        cat = Categorie(beschrijving="Test categorie")
        cat.save()

        Vraag(
            categorie=cat,
            vraag_tekst='Vraag nummer 1',
            antwoord_a='Morgen',
            antwoord_b='Overmorgen',
            antwoord_c='Gisteren',
            antwoord_d='Volgende week',
            juiste_antwoord='A').save()

        Vraag(
            # categorie=cat,            # bewust niet gezet voor meer coverage
            vraag_tekst='Vraag nummer 2',
            antwoord_a='Geel',
            antwoord_b='Rood',
            antwoord_c='Blauw',
            antwoord_d='Wit',
            juiste_antwoord='B').save()

        Vraag(
            categorie=cat,
            is_actief=False,        # mag niet getoond worden
            gebruik_voor_toets=True,
            gebruik_voor_quiz=True,
            vraag_tekst='Inactief mag niet getoond worden',
            antwoord_a='Ja',
            antwoord_b='Nee',
            antwoord_c='Nja',
            antwoord_d='',
            juiste_antwoord='B').save()

        bulk = [Vraag(
                    categorie=cat,
                    vraag_tekst='Vraag nummer %s' % (3 + nr),
                    antwoord_a='Geel',
                    antwoord_b='Rood',
                    antwoord_c='Blauw',
                    antwoord_d='Wit',
                    juiste_antwoord='A')
                for nr in range(20)]
        Vraag.objects.bulk_create(bulk)

    def test_anon(self):
        resp = self.client.get(self.url_begin)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_uitslag)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_volgende_vraag)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_ontvang_antwoord)
        self.assert403(resp, "Geen toegang")

    def test_gast(self):
        self.account_100000.is_gast = True
        self.account_100000.save(update_fields=['is_gast'])
        self.e2e_login(self.account_100000)

        resp = self.client.get(self.url_begin)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_uitslag)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_volgende_vraag)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_ontvang_antwoord)
        self.assert403(resp, "Geen toegang")

    def test_begin(self):
        self.e2e_login(self.account_100000)

        # toets is nog niet opgestart
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/begin-toets.dtl', 'plein/site_layout.dtl'))

        # start de toets op
        self.assertEqual(Instaptoets.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)

        # nog een keer start geen nieuwe toets op
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)

        toets = Instaptoets.objects.first()
        self.assertEqual(str(toets.afgerond)[:10], '9999-12-31')
        self.assertEqual(toets.sporter, self.sporter_100000)
        self.assertEqual(toets.aantal_vragen, 20)
        self.assertEqual(toets.aantal_antwoorden, 0)
        self.assertEqual(toets.is_afgerond, False)
        self.assertEqual(toets.aantal_goed, 0)
        self.assertEqual(toets.geslaagd, False)
        self.assertEqual(toets.vraag_antwoord.count(), 20)
        self.assertTrue(str(toets) != '')

        # controleer dat geen inactieve vraag geselecteerd is
        for vraag_antwoord in toets.vraag_antwoord.all():
            vraag = vraag_antwoord.vraag
            self.assertTrue(vraag.is_actief)
            self.assertTrue(vraag.gebruik_voor_toets)
            self.assertTrue(str(vraag) != '')
            self.assertTrue(str(vraag.categorie) != '')
        # for

        # get terwijl er al een toets gestart is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/begin-toets.dtl', 'plein/site_layout.dtl'))

        # GET terwijl er al een afgeronde toets is, maar de sporter niet geslaagd is
        toets_zet_afgerond_niet_geslaagd(toets)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/begin-toets.dtl', 'plein/site_layout.dtl'))

        # GET terwijl er al een afgeronde maar nog wel geldige toets is
        toets_zet_geslaagd_nog_geldig(toets)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/begin-toets.dtl', 'plein/site_layout.dtl'))

        # GET terwijl er al een afgeronde maar niet meer geldige toets is
        toets_zet_geslaagd_niet_meer_geldig(toets)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/begin-toets.dtl', 'plein/site_layout.dtl'))

    def test_uitslag(self):
        self.e2e_login(self.account_100000)

        # GET terwijl er geen toets gestart is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag)
        self.assert_is_redirect(resp, self.url_begin)

        # start de toets op
        self.assertEqual(Instaptoets.objects.count(), 0)
        resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()

        # GET terwijl de toets nog niet afgerond is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag)
        self.assert_is_redirect(resp, self.url_begin)

        # GET van een afgeronde toets
        toets_zet_afgerond_niet_geslaagd(toets)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/toon-uitslag.dtl', 'plein/site_layout.dtl'))

    def test_volgende_vraag(self):
        self.e2e_login(self.account_100000)

        # get terwijl er geen toets gestart is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assert_is_redirect(resp, self.url_begin)

        # start de toets op
        self.assertEqual(Instaptoets.objects.count(), 0)
        resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()

        # get the volgende vraag
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/volgende-vraag.dtl', 'plein/site_layout.dtl'))

        # laatste vraag --> geen overslaan knop
        toets.aantal_antwoorden = toets.aantal_vragen - 1
        toets.save(update_fields=['aantal_antwoorden'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/volgende-vraag.dtl', 'plein/site_layout.dtl'))

        # geen valide vraag
        self.assertTrue(str(toets.vraag_antwoord.first()) != '')
        toets.vraag_antwoord.clear()
        toets.huidige_vraag = None
        toets.save(update_fields=['huidige_vraag'])
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assert404(resp, 'Toets is niet beschikbaar')

        # get terwijl er de toets al afgerond is
        toets_zet_afgerond_niet_geslaagd(toets)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_volgende_vraag)
        self.assert_is_redirect(resp, self.url_uitslag)

    def test_ontvang_antwoord(self):
        self.e2e_login(self.account_100000)

        # get terwijl er geen toets gestart is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ontvang_antwoord)
        self.assert_is_redirect(resp, self.url_begin)

        # start de toets op
        self.assertEqual(Instaptoets.objects.count(), 0)
        resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()

        # get terwijl er een toets gestart is --> get wordt niet ondersteund
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ontvang_antwoord)
        self.assertEqual(resp.status_code, 405)

        # vraag overslaan (post zonder keuze)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ontvang_antwoord)
        self.assert_is_redirect(resp, self.url_volgende_vraag)

        # niet ondersteund antwoord is ook "volgende vraag"
        resp = self.client.post(self.url_ontvang_antwoord, {'keuze': 'E'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)

        # post het antwoord: verzoek tot overslaan
        self.assertEqual(toets.aantal_antwoorden, 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ontvang_antwoord, {'keuze': 'overslaan'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        toets.refresh_from_db()
        self.assertEqual(toets.aantal_antwoorden, 0)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ontvang_antwoord, {'keuze': 'D'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        toets.refresh_from_db()
        self.assertEqual(toets.aantal_antwoorden, 1)

        # wijzig een antwoord (dit kan in de praktijk niet voorkomen)
        toets.huidige_vraag.antwoord = 'B'
        toets.huidige_vraag.save(update_fields=['antwoord'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ontvang_antwoord, {'keuze': 'A'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)

        toets.aantal_antwoorden = toets.aantal_vragen - 1
        toets.save(update_fields=['aantal_antwoorden'])
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ontvang_antwoord, {'keuze': 'A'})
        self.assert_is_redirect(resp, self.url_uitslag)

        # get terwijl er de toets al afgerond is
        toets_zet_afgerond_niet_geslaagd(toets)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ontvang_antwoord)
        self.assert_is_redirect(resp, self.url_uitslag)

    def test_geslaagd(self):
        self.e2e_login(self.account_100000)

        # start de toets op
        resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)

        # antwoord A is bijna altijd de juiste
        for lp in range(20):
            resp = self.client.post(self.url_ontvang_antwoord, {'keuze': 'A'})
        # for
        self.assert_is_redirect(resp, self.url_uitslag)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/toon-uitslag.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Gefeliciteerd')

    def test_operations(self):
        # corner cases
        self.e2e_login(self.account_100000)

        # start de toets op
        self.assertEqual(Instaptoets.objects.count(), 0)
        resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()

        toets.vraag_antwoord.clear()
        selecteer_huidige_vraag(toets, forceer=True)

        toets.is_afgerond = True
        selecteer_huidige_vraag(toets)

    def test_geen_toets(self):
        # maak de toets "niet beschikbaar"
        Vraag.objects.all().delete()

        self.e2e_login(self.account_100000)

        # get terwijl er geen instaptoets is
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_begin)
        self.assert_is_redirect(resp, self.url_opleiding_overzicht)

    def test_opnieuw_na_gezakt(self):
        self.e2e_login(self.account_100000)

        # start de toets op
        self.assertEqual(Instaptoets.objects.count(), 0)
        resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()

        toets_zet_afgerond_niet_geslaagd(toets)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 2)

    def test_opnieuw_forced_restart(self):
        # op de test server kan de toets opnieuw gestart worden als deze al gehaald is
        self.e2e_login(self.account_100000)

        # start de toets op
        self.assertEqual(Instaptoets.objects.count(), 0)
        resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()

        # expliciet restart verzoek werkt niet, want niet op test server
        toets_zet_geslaagd_nog_geldig(toets)
        with override_settings(IS_TEST_SERVER=False):
            resp = self.client.post(self.url_begin, {'opnieuw': 'J'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)

        # expliciet restart verzoek op de test server
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_begin, {'opnieuw': 'J'})
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 2)

        Instaptoets.objects.exclude(pk=toets.pk).delete()
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets_zet_afgerond_niet_geslaagd(toets)

    def test_opnieuw_verlopen(self):
        # op de test server kan de toets opnieuw gestart worden als deze al gehaald is
        self.e2e_login(self.account_100000)

        # start de toets op
        self.assertEqual(Instaptoets.objects.count(), 0)
        resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)
        toets = Instaptoets.objects.first()

        toets_zet_geslaagd_nog_geldig(toets)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 1)

        toets_zet_geslaagd_niet_meer_geldig(toets)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_begin)
        self.assert_is_redirect(resp, self.url_volgende_vraag)
        self.assertEqual(Instaptoets.objects.count(), 2)


# end of file
