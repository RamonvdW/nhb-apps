# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from Bestelling.definities import (BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_AFGEROND,
                                   BESTELLING_REGEL_CODE_WEBWINKEL)
from Bestelling.models import Bestelling, BestellingRegel
from Betaal.models import BetaalInstellingenVereniging
from Geo.models import Regio
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from decimal import Decimal
import datetime


class TestBestellingOmzet(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, module Omzet """

    url_omzet_alles = '/bestel/omzet/alles/'
    url_omzet_leden = '/bestel/omzet/exclusief-bondsbureau/'

    volgende_bestel_nr = 1234567

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save(update_fields=['is_BB'])

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

        # maak een verkopende vereniging
        ver = Vereniging(
                    naam="Verkopende Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(regio_nr=111))
        ver.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            mollie_api_key='test_1235')
        instellingen.save()
        self.instellingen_ver = instellingen

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

        regel = BestellingRegel(
                        korte_beschrijving='webwinkel 1',
                        bedrag_euro=Decimal(1.23),
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()
        bestelling.regels.add(regel)

        regel = BestellingRegel(
                        korte_beschrijving='webwinkel 2',
                        bedrag_euro=Decimal(10.00),
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()
        bestelling.regels.add(regel)

        # bestelling van een verkopende vereniging
        bestelling = Bestelling(
                        bestel_nr=1236,
                        account=self.account_admin,
                        ontvanger=self.instellingen_ver,
                        verkoper_naam='Ver naam',
                        verkoper_adres1='Ver adres 1',
                        verkoper_adres2='Ver adres 2',
                        verkoper_kvk='Ver Kvk',
                        verkoper_email='contact@ver.not',
                        verkoper_telefoon='0123456799',
                        verkoper_iban='NL2BANK0123456799',
                        verkoper_bic='VER2BIC',
                        verkoper_heeft_mollie=False,
                        totaal_euro='10.00',
                        status=BESTELLING_STATUS_BETALING_ACTIEF,
                        log='Een beginnetje\n')
        bestelling.save()

        # nog een bestelling van een verkopende vereniging
        bestelling = Bestelling(
                        bestel_nr=1237,
                        account=self.account_admin,
                        ontvanger=self.instellingen_ver,
                        verkoper_naam='Ver naam',
                        verkoper_adres1='Ver adres 1',
                        verkoper_adres2='Ver adres 2',
                        verkoper_kvk='Ver Kvk',
                        verkoper_email='contact@ver.not',
                        verkoper_telefoon='0123456799',
                        verkoper_iban='NL2BANK0123456799',
                        verkoper_bic='VER2BIC',
                        verkoper_heeft_mollie=False,
                        totaal_euro='11.00',
                        status=BESTELLING_STATUS_BETALING_ACTIEF,
                        log='Een beginnetje\n')
        bestelling.save()

        # gratis bestelling
        bestelling = Bestelling(
                        bestel_nr=1238,
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
                        totaal_euro='0.00',
                        status=BESTELLING_STATUS_AFGEROND,
                        log='Gratis\n')
        bestelling.save()

        # bestelling in een ander jaar
        bestelling = Bestelling(
                        bestel_nr=1239,
                        account=self.account_admin,
                        ontvanger=self.instellingen_ver,
                        verkoper_naam='Ver naam',
                        verkoper_adres1='Ver adres 1',
                        verkoper_adres2='Ver adres 2',
                        verkoper_kvk='Ver Kvk',
                        verkoper_email='contact@ver.not',
                        verkoper_telefoon='0123456799',
                        verkoper_iban='NL2BANK0123456799',
                        verkoper_bic='VER2BIC',
                        verkoper_heeft_mollie=False,
                        totaal_euro='10.00',
                        status=BESTELLING_STATUS_BETALING_ACTIEF,
                        log='Een beginnetje\n')
        bestelling.save()
        bestelling.aangemaakt -= datetime.timedelta(days=366)       # ander jaar
        bestelling.save(update_fields=['aangemaakt'])

    def test_anon(self):
        # inlog vereist
        self.client.logout()
        resp = self.client.get(self.url_omzet_alles)
        self.assert403(resp)
        resp = self.client.get(self.url_omzet_leden)
        self.assert403(resp)

        # geen is_staff vlag
        self.account_admin.is_staff = False
        self.account_admin.save(update_fields=['is_staff'])

        resp = self.client.get(self.url_omzet_alles)
        self.assert403(resp)
        resp = self.client.get(self.url_omzet_leden)
        self.assert403(resp)

    def test_omzet(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_omzet_alles)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/omzet.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_omzet_leden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/omzet.dtl', 'design/site_layout.dtl'))


# end of file
