# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Competitie.models import competitie_aanmaken, DeelCompetitie
from Functie.models import maak_functie
from Mailer.models import MailQueue
from Overig.e2ehelpers import E2EHelpers


class TestFunctieWijzigEmail(E2EHelpers, TestCase):
    """ unit tests voor de Functie applicatie; module VHPG """

    test_after = ('Functie.test_2fa', 'Functie.wisselvanrol')

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal', accepteer_vhpg=True)

        rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        regio_101 = NhbRegio.objects.get(regio_nr=101)
        regio_105 = NhbRegio.objects.get(regio_nr=105)

        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        deel1 = DeelCompetitie.objects.filter(laag='BK')[0]
        self.functie_bko1 = deel1.functie
        self.functie_bko2 = DeelCompetitie.objects.filter(laag='BK')[1].functie
        self.functie_rko1 = DeelCompetitie.objects.filter(laag='RK', competitie=deel1.competitie, nhb_rayon=rayon_1)[0].functie
        self.functie_rcl101 = DeelCompetitie.objects.filter(laag='Regio', competitie=deel1.competitie, nhb_regio=regio_101)[0].functie
        self.functie_rcl105 = DeelCompetitie.objects.filter(laag='Regio', competitie=deel1.competitie, nhb_regio=regio_105)[0].functie

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = regio_105
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        self.functie_cwz = maak_functie("CWZ test", "CWZ")
        self.functie_cwz.nhb_ver = ver
        self.functie_cwz.save()

        self.url_wijzig_email = '/functie/wijzig-email/%s/'  # % functie_pk

    def _check_wijzigbaar(self, functie):
        url = self.url_wijzig_email % functie.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig-email.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post(url, {'email': 'nieuweemail@test.com'})
        self.assertEqual(resp.status_code, 302)
        # precies waar de redirect heen gaat is niet belangrijk

    def _check_niet_wijzigbaar(self, functie):
        url = self.url_wijzig_email % functie.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post(url, {'email': 'nieuweemail@test.com'})
        self.assertEqual(resp.status_code, 404)

    def test_get_anon(self):
        url = self.url_wijzig_email % self.functie_rko1.pk
        resp = self.client.get(url)
        self.assert_is_redirect(resp, '/plein/')

    def test_bb(self):
        # log in en wissel naar BB rol
        self.account_normaal.is_BB = True
        self.account_normaal.save()
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wisselnaarrol_bb()

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        count_pre = len(MailQueue.objects.all())

        self._check_wijzigbaar(self.functie_bko1)
        self._check_wijzigbaar(self.functie_bko2)
        self._check_niet_wijzigbaar(self.functie_rko1)
        self._check_niet_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_cwz)

        count_post = len(MailQueue.objects.all())
        self.assertEqual(count_pre + 2, count_post)

        # volg de tijdelijke URL in de email
        mail = MailQueue.objects.all()[0]
        text = mail.mail_text
        pos = text.find('/overig/url/')     # 12 lang
        url = text[pos:pos+12+32+1]        # 32 = code

        resp = self.client.get(url)
        self.assert_equal(resp.status_code, 200)
        self.assert_template_used(resp, ('functie/bevestigd.dtl', 'plein/site_layout.dtl'))

    def test_bko1(self):
        # log in en wissel naar BKO 1
        self.functie_bko1.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_bko1)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_wijzigbaar(self.functie_bko1)
        self._check_niet_wijzigbaar(self.functie_bko2)
        self._check_wijzigbaar(self.functie_rko1)           # want zelfde comp_type als bko1
        self._check_niet_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_cwz)

    def test_bko2(self):
        # log in en wissel naar BKO 2
        self.functie_bko2.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_bko2)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_niet_wijzigbaar(self.functie_bko1)
        self._check_wijzigbaar(self.functie_bko2)
        self._check_niet_wijzigbaar(self.functie_rko1)      # want NIET zelfde comp_type als bko1
        self._check_niet_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_cwz)

    def test_rko1(self):
        # log in en wissel naar RKO Rayon 1 rol
        self.functie_rko1.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_rko1)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_niet_wijzigbaar(self.functie_bko1)
        self._check_niet_wijzigbaar(self.functie_bko2)
        self._check_wijzigbaar(self.functie_rko1)
        self._check_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_cwz)

    def test_rcl101(self):
        # log in en wissel naar RCL regio 101
        self.functie_rcl101.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_rcl101)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_niet_wijzigbaar(self.functie_bko1)
        self._check_niet_wijzigbaar(self.functie_bko2)
        self._check_niet_wijzigbaar(self.functie_rko1)
        self._check_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_cwz)

    def test_rcl105(self):
        # log in en wissel naar RCL regio 105
        self.functie_rcl105.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_rcl105)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_niet_wijzigbaar(self.functie_bko1)
        self._check_niet_wijzigbaar(self.functie_bko2)
        self._check_niet_wijzigbaar(self.functie_rko1)
        self._check_niet_wijzigbaar(self.functie_rcl101)
        self._check_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_cwz)

    def test_cwz(self):
        # log in en wissel naar CWZ
        self.functie_cwz.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_cwz)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_niet_wijzigbaar(self.functie_bko1)
        self._check_niet_wijzigbaar(self.functie_bko2)
        self._check_niet_wijzigbaar(self.functie_rko1)
        self._check_niet_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_wijzigbaar(self.functie_cwz)

    def test_bad(self):
        # log in en wissel naar RKO rol
        self.functie_rko1.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_rko1)

        # niet bestaande functie
        url = self.url_wijzig_email % 999999
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)

        # post met te weinig parameters
        url = self.url_wijzig_email % self.functie_rko1.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'E-mailadres niet geaccepteerd')

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

# end of file
