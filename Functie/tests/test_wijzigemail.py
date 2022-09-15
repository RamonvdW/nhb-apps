# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Competitie.models import DeelCompetitie, LAAG_BK, LAAG_RK, LAAG_REGIO
from Competitie.operations import competities_aanmaken
from Functie.operations import maak_functie, Functie
from Mailer.models import MailQueue
from Overig.models import SiteTijdelijkeUrl
from TestHelpers.e2ehelpers import E2EHelpers


class TestFunctieWijzigEmail(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie; module wijzig functie e-mail """

    test_after = ('Functie.test_2fa', 'Functie.wisselvanrol')

    url_wijzig_email = '/functie/wijzig-email/%s/'  # % functie_pk

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal', accepteer_vhpg=True)

        rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        regio_101 = NhbRegio.objects.get(regio_nr=101)
        regio_105 = NhbRegio.objects.get(regio_nr=105)

        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=2019)

        deel1 = DeelCompetitie.objects.filter(laag=LAAG_BK)[0]
        self.functie_bko1 = deel1.functie
        self.functie_bko2 = DeelCompetitie.objects.filter(laag=LAAG_BK)[1].functie
        self.functie_rko1 = DeelCompetitie.objects.filter(laag=LAAG_RK, competitie=deel1.competitie, nhb_rayon=rayon_1)[0].functie
        self.functie_rcl101 = DeelCompetitie.objects.filter(laag=LAAG_REGIO, competitie=deel1.competitie, nhb_regio=regio_101)[0].functie
        self.functie_rcl105 = DeelCompetitie.objects.filter(laag=LAAG_REGIO, competitie=deel1.competitie, nhb_regio=regio_105)[0].functie

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = regio_105
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

    def _check_wijzigbaar(self, functie):
        url = self.url_wijzig_email % functie.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/wijzig-email.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'email': 'nieuweemail@test.com'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/bevestig.dtl', 'plein/site_layout.dtl'))

    def _check_niet_wijzigbaar(self, functie):
        url = self.url_wijzig_email % functie.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'email': 'nieuweemail@test.com'})
        self.assert403(resp)

    def test_get_anon(self):
        url = self.url_wijzig_email % self.functie_rko1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

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
        self._check_niet_wijzigbaar(self.functie_hwl)
        self._check_niet_wijzigbaar(self.functie_wl)

        count_post = len(MailQueue.objects.all())
        self.assertEqual(count_pre + 2, count_post)

        # volg de tijdelijke URL in de email
        mail = MailQueue.objects.all()[0]
        text = mail.mail_text
        pos = text.find('/overig/url/')     # 12 lang
        url = text[pos:pos+12+32+1]        # 32 = code

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
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
        self._check_niet_wijzigbaar(self.functie_hwl)
        self._check_niet_wijzigbaar(self.functie_wl)

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
        self._check_niet_wijzigbaar(self.functie_hwl)
        self._check_niet_wijzigbaar(self.functie_wl)

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
        self._check_niet_wijzigbaar(self.functie_hwl)
        self._check_niet_wijzigbaar(self.functie_wl)

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
        self._check_niet_wijzigbaar(self.functie_hwl)       # verkeerde regio
        self._check_niet_wijzigbaar(self.functie_wl)        # verkeerde regio

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
        self._check_wijzigbaar(self.functie_hwl)            # juiste regio
        self._check_wijzigbaar(self.functie_wl)             # juiste regio

    def test_hwl(self):
        # log in en wissel naar HWL
        self.functie_hwl.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_niet_wijzigbaar(self.functie_bko1)
        self._check_niet_wijzigbaar(self.functie_bko2)
        self._check_niet_wijzigbaar(self.functie_rko1)
        self._check_niet_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_sec)
        self._check_wijzigbaar(self.functie_hwl)
        self._check_wijzigbaar(self.functie_wl)

    def test_sec(self):
        # log in en wissel naar SEC
        self.functie_sec.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_sec)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_niet_wijzigbaar(self.functie_bko1)
        self._check_niet_wijzigbaar(self.functie_bko2)
        self._check_niet_wijzigbaar(self.functie_rko1)
        self._check_niet_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_sec)
        self._check_wijzigbaar(self.functie_hwl)
        self._check_wijzigbaar(self.functie_wl)

    def test_wl(self):
        # log in en wissel naar WL
        self.functie_wl.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_wl)

        # controleer dat de juiste e-mailadressen wel/niet wijzigbaar zijn
        self._check_niet_wijzigbaar(self.functie_bko1)
        self._check_niet_wijzigbaar(self.functie_bko2)
        self._check_niet_wijzigbaar(self.functie_rko1)
        self._check_niet_wijzigbaar(self.functie_rcl101)
        self._check_niet_wijzigbaar(self.functie_rcl105)
        self._check_niet_wijzigbaar(self.functie_sec)
        self._check_niet_wijzigbaar(self.functie_hwl)
        self._check_wijzigbaar(self.functie_wl)

    def test_multi_change(self):
        # voer meerdere malen een e-mailadres is
        # volg daarna een van de tijdelijke urls

        # log in en wissel naar RCL regio 105
        self.functie_rcl105.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_rcl105)

        url = self.url_wijzig_email % self.functie_rcl105.pk

        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 0)

        # eerste invoer
        with self.assert_max_queries(8):
            resp = self.client.post(url, {'email': 'nieuweemail1@test.com'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/bevestig.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 1)

        # controleer dat het nieuwe e-mailadres gezet is
        functie = Functie.objects.get(pk=self.functie_rcl105.pk)
        self.assertEqual(functie.nieuwe_email, 'nieuweemail1@test.com')
        self.assertEqual(functie.bevestigde_email, '')

        # check dat een mail aangemaakt is
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.all()[0]
        self.assert_email_html_ok(mail.mail_html, 'email_functie/bevestig-toegang-email.dtl')
        self.assert_consistent_email_html_text(mail)

        # haal de 1e tijdelijke url op
        mail = MailQueue.objects.order_by('-toegevoegd_op')[0]
        text = mail.mail_text
        pos = text.find('/overig/url/')     # 12 = deze url lengte
        url1 = text[pos:pos+12+32+1]         # 32 = code

        # tweede invoer
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'email': 'nieuweemail2@test.com'})
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/bevestig.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 2)

        # controleer dat het nieuwe e-mailadres gezet is
        functie = Functie.objects.get(pk=self.functie_rcl105.pk)
        self.assertEqual(functie.nieuwe_email, 'nieuweemail2@test.com')
        self.assertEqual(functie.bevestigde_email, '')

        # haal de 2e tijdelijke url op
        mail = MailQueue.objects.order_by('-toegevoegd_op')[0]
        text = mail.mail_text
        pos = text.find('/overig/url/')     # 12 = deze url lengte
        url2 = text[pos:pos+12+32+1]         # 32 = code

        # volg de 1e url
        with self.assert_max_queries(20):
            resp = self.client.get(url1)
        self.assertEqual(resp.status_code, 200)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/bevestigd.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 1)

        # controleer dat het laatste nieuwe e-mailadres gezet is
        functie = Functie.objects.get(pk=self.functie_rcl105.pk)
        self.assertEqual(functie.nieuwe_email, '')
        self.assertEqual(functie.bevestigde_email, 'nieuweemail2@test.com')

        # volg de 2e url
        with self.assert_max_queries(20):
            resp = self.client.get(url2)
        self.assertEqual(resp.status_code, 200)
        urls = self.extract_all_urls(resp, skip_menu=True, skip_smileys=True)
        post_url = urls[0]
        with self.assert_max_queries(20):
            resp = self.client.post(post_url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('functie/bevestigd.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(SiteTijdelijkeUrl.objects.count(), 0)

        # controleer dat het laatste nieuwe e-mailadres gezet is
        functie = Functie.objects.get(pk=self.functie_rcl105.pk)
        self.assertEqual(functie.nieuwe_email, '')
        self.assertEqual(functie.bevestigde_email, 'nieuweemail2@test.com')

    def test_bad(self):
        # log in en wissel naar RKO rol
        self.functie_rko1.accounts.add(self.account_normaal)
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_rko1)

        # niet bestaande functie
        url = self.url_wijzig_email % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Foutieve functie')
        resp = self.client.post(url)
        self.assert404(resp, 'Foutieve functie')

        # post met te weinig parameters
        url = self.url_wijzig_email % self.functie_rko1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'E-mailadres niet geaccepteerd')

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

# end of file
