# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import CompetitieIndivKlasse
from CompLaagBond.models import KampBK, CutBK
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompetitiePlanningBond(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, planning voor het BK """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_limieten = '/bondscompetities/bk/planning/%s/limieten/'   # deelkamp_pk

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_bondscompetities()

        self.account_bb = data.account_bb

        self.deelkamp_bk_18 = KampBK.objects.filter(competitie=data.comp18).first()

        self.functie_bko_18 = self.deelkamp_bk_18.functie
        self.functie_bko_18.accounts.add(self.account_bb)

        self.deelkamp_bk_25 = KampBK.objects.filter(competitie=data.comp25).first()

        qset = CompetitieIndivKlasse.objects.filter(competitie=data.comp18,
                                                    boogtype__afkorting='R',
                                                    is_ook_voor_rk_bk=True)
        self.klasse_indiv_r0 = qset[0]
        self.klasse_indiv_r1 = qset[1]

        CutBK.objects.create(
            kamp=self.deelkamp_bk_18,
            indiv_klasse=self.klasse_indiv_r0,
            limiet=24)

    def test_limieten(self):
        # anon test
        self.client.logout()
        resp = self.client.get(self.url_limieten % 999999)
        self.assert403(resp)

        # wordt BKO
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        # verkeerde BKO
        url = self.url_limieten % self.deelkamp_bk_25.pk
        resp = self.client.get(url)
        self.assert404(resp, 'Niet de beheerder')

        resp = self.client.post(url)
        self.assert404(resp, 'Niet de beheerder')

        url = self.url_limieten % self.deelkamp_bk_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/wijzig-limieten.dtl', 'design/site_layout.dtl'))

        isel_r0 = 'isel_%s' % self.klasse_indiv_r0.pk
        isel_r1 = 'isel_%s' % self.klasse_indiv_r1.pk

        # wijzig limieten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {isel_r0: 24, isel_r1: 8, 'snel': '1'})
        self.assert_is_redirect_not_plein(resp)

        # corner cases
        resp = self.client.post(url, {isel_r0: 0})
        self.assert404(resp, 'Geen valide keuze voor indiv')

        resp = self.client.post(url, {isel_r0: 'xx'})
        self.assert_is_redirect_not_plein(resp)

        url = self.url_limieten % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.post(url)
        self.assert404(resp, 'Kampioenschap niet gevonden')


# end of file
