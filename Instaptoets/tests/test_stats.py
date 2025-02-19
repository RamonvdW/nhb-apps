# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Geo.models import Regio
from Instaptoets.models import Categorie, Vraag, ToetsAntwoord, Instaptoets
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestInstaptoetsStats(E2EHelpers, TestCase):

    """ tests voor de Instaptoets applicatie, module view_stats """

    test_after = ('Sporter.tests.test_login',)

    url_stats = '/opleiding/instaptoets/stats/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_100000)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_100000)

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
            gebruik_voor_quiz=True,             # toets + quiz
            vraag_tekst='Vraag nummer 1',
            antwoord_a='Morgen',
            antwoord_b='Overmorgen',
            antwoord_c='Gisteren',
            antwoord_d='Volgende week',
            juiste_antwoord='D').save()

        Vraag(
            categorie=cat,
            vraag_tekst='Vraag nummer 2',
            antwoord_a='Geel',
            antwoord_b='Rood',
            antwoord_c='',
            antwoord_d='',
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
            juiste_antwoord='C').save()

        rot = "ABCD" * 6
        bulk = [Vraag(
                    categorie=cat,
                    vraag_tekst='Vraag nummer %s' % (3 + nr),
                    antwoord_a='Geel',
                    antwoord_b='Rood',
                    antwoord_c='Blauw',
                    antwoord_d='Wit',
                    juiste_antwoord=rot[nr])
                for nr in range(20)]
        Vraag.objects.bulk_create(bulk)

        bulk = list()
        rot = "ABCD"
        for vraag in Vraag.objects.all():
            antwoord = ToetsAntwoord(
                                vraag=vraag,
                                antwoord=rot[0])
            rot = rot[1:] + rot[0]
            bulk.append(antwoord)
        # for
        bulk.pop(-1)
        ToetsAntwoord.objects.bulk_create(bulk)

        Vraag(
            categorie=cat,
            gebruik_voor_toets=False,
            gebruik_voor_quiz=True,
            vraag_tekst='Vraag voor de quiz',
            antwoord_a='Geel',
            antwoord_b='Rood',
            antwoord_c='',
            antwoord_d='',
            juiste_antwoord='B').save()

    def test_anon(self):
        resp = self.client.get(self.url_stats)
        self.assert403(resp, "Geen toegang")

        # instaptoets niet beschikbaar
        Vraag.objects.all().delete()
        resp = self.client.get(self.url_stats)
        self.assert_is_redirect(resp, '/opleiding/')

    def test_stats(self):
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_mo)

        # toets is nog niet opgestart
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_stats)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/stats-antwoorden.dtl', 'plein/site_layout.dtl'))

        # maak een paar toetsen aan
        Instaptoets(
            sporter=self.sporter_100000,
            aantal_vragen=20,
            aantal_antwoorden=20,
            is_afgerond=False,
        ).save()

        Instaptoets(
            sporter=self.sporter_100000,
            aantal_vragen=20,
            aantal_antwoorden=20,
            is_afgerond=True,
            aantal_goed=1,
            geslaagd=False,
        ).save()

        Instaptoets(
            sporter=self.sporter_100000,
            aantal_vragen=20,
            aantal_antwoorden=20,
            is_afgerond=True,
            aantal_goed=18,
            geslaagd=False,
        ).save()

        # toets is nog niet opgestart
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_stats)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('instaptoets/stats-antwoorden.dtl', 'plein/site_layout.dtl'))


# end of file
