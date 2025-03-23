# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Bestelling.definities import (BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING,
                                   BESTELLING_REGEL_CODE_OPLEIDING, BESTELLING_REGEL_CODE_EVENEMENT)
from Bestelling.models import Bestelling, BestellingRegel
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_PAYMENT
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Functie.models import Functie
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from decimal import Decimal
import datetime


class TestBestellingActiviteit(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, module Activiteit """

    test_after = ('Bestelling.tests.test_mandje',)

    url_activiteit = '/bestel/activiteit/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save(update_fields=['is_BB'])

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(regio_nr=111))
        ver.save()

        # maak het lid aan die MWW word
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Manager",
                    achternaam="Webwinkel",
                    email="mww@khsn.not",
                    geboorte_datum=datetime.date(year=1992, month=3, day=4),
                    sinds_datum=datetime.date(year=2013, month=12, day=11),
                    bij_vereniging=ver)
        sporter.save()

        self.account_mww = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

        self.functie_mww = Functie.objects.filter(rol='MWW').first()
        self.functie_mww.accounts.add(self.account_mww)

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

        bestelling = Bestelling(
                        bestel_nr=1235,
                        account=self.account_admin,
                        ontvanger=self.instellingen_bond,
                        verkoper_naam='Ver naam',
                        verkoper_adres1='Ver adres 1',
                        verkoper_adres2='Ver adres 2',
                        verkoper_kvk='Ver Kvk',
                        verkoper_email='contact@ver.not',
                        verkoper_telefoon='0123456799',
                        verkoper_iban='NL2BANK0123456799',
                        verkoper_bic='VER2BIC',
                        verkoper_heeft_mollie=False,
                        totaal_euro='1.23',
                        status=BESTELLING_STATUS_BETALING_ACTIEF,
                        log='Een beginnetje\n')
        bestelling.save()
        self.bestelling = bestelling

        regel = BestellingRegel(
                        korte_beschrijving='webwinkel',
                        bedrag_euro=Decimal(1.23),
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()
        bestelling.regels.add(regel)

        regel = BestellingRegel(
                        korte_beschrijving='evenement',
                        bedrag_euro=Decimal('1.23'),
                        code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()
        bestelling.regels.add(regel)

        regel = BestellingRegel(
                        korte_beschrijving='opleiding',
                        bedrag_euro=Decimal('50.00'),
                        code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()
        bestelling.regels.add(regel)

        regel = BestellingRegel(
                        korte_beschrijving='wedstrijd',
                        bedrag_euro=Decimal('14.34'),
                        code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()
        bestelling.regels.add(regel)

        # speciale code die niet in de top-4 staat
        regel = BestellingRegel(
                        korte_beschrijving='korting',
                        bedrag_euro=Decimal('2.50'),
                        code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
        regel.save()
        bestelling.regels.add(regel)

        transactie = BetaalTransactie(
                            when=timezone.now(),
                            bedrag_handmatig=10)
        transactie.save()
        bestelling.transacties.add(transactie)

        transactie = BetaalTransactie(
                            when=timezone.now(),
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                            payment_id='test',
                            payment_status='test',
                            bedrag_te_ontvangen=10,
                            bedrag_terugbetaald=5,
                            bedrag_teruggevorderd=4)
        transactie.save()
        bestelling.transacties.add(transactie)

    def test_anon(self):
        # inlog vereist
        self.client.logout()
        resp = self.client.get(self.url_activiteit)
        self.assert403(resp)

    def test_zoek(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        # geen zoekterm
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # slechte zoekterm (veel te lang)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=' + 'haha' * 100)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # lege zoekterm, gratis filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&gratis=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # lege zoekterm, evenementen filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&evenementen=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # lege zoekterm, webwinkel filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&webwinkel=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # lege zoekterm, wedstrijden filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&wedstrijden=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # lege zoekterm, opleidingen filter
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=&opleidingen=on')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm getal
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=1234')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm tekst
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=test')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm bestelnummer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=MH-1234')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # zoekterm nog te betalen / mislukte betalingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit + '?zoekterm=**')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

        # geen top-4
        BestellingRegel.objects.exclude(code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING).delete()

        # geen mollie transactie
        BetaalTransactie.objects.filter(transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT).delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))

    def test_mww(self):
        # controleer dat de MWW ook bij de bestellingen pagina kan

        self.e2e_login_and_pass_otp(self.account_mww)
        self.e2e_wissel_naar_functie(self.functie_mww)

        # geen bestellingen, geen zoekterm
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_activiteit)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/activiteit.dtl', 'plein/site_layout.dtl'))


# end of file
