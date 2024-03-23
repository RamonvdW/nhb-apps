# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.definities import DEELNAME_ONBEKEND
from Competitie.models import KampioenschapIndivKlasseLimiet, KampioenschapSporterBoog, CompetitieMutatie
from Competitie.test_utils.tijdlijn import zet_competitie_fase_bk_wedstrijden, zet_competitie_fase_rk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagBondIndiv(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, Indiv views """

    test_after = ('Competitie.tests.test_overzicht', 'CompBeheer.tests.test_bko')

    url_bk_selectie = '/bondscompetities/bk/selectie/%s/'                               # deelkamp_pk
    url_bk_selectie_download = '/bondscompetities/bk/selectie/%s/bestand/'              # deelkamp_pk
    url_wijzig_status = '/bondscompetities/bk/selectie/wijzig-status-bk-deelnemer/%s/'  # deelnemer_pk

    testdata = None
    deelnemers_no_ver = list()

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()

        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        for regio_nr in (111, 113):
            ver_nr = data.regio_ver_nrs[regio_nr][0]
            data.maak_rk_deelnemers(18, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])
            data.maak_rk_teams(18, ver_nr, zet_klasse=True)
        # for

        data.maak_uitslag_rk_indiv(18)
        data.maak_bk_deelnemers(18)
        data.maak_bk_teams(18)

        # we hebben heel veel sporters in Recurve klasse 6
        # (waarschijnlijk omdat de klassengrenzen niet vastgesteld zijn)
        kamp = KampioenschapSporterBoog.objects.filter(kampioenschap=data.deelkamp18_bk, volgorde=20).first()
        grote_klasse = kamp.indiv_klasse
        KampioenschapIndivKlasseLimiet(kampioenschap=data.deelkamp18_bk, indiv_klasse=grote_klasse, limiet=8).save()

        # zet een sporter met kampioen label op 'deelname onzeker'
        kampioen = KampioenschapSporterBoog.objects.exclude(kampioen_label='').order_by('pk')[0]
        kampioen.deelname = DEELNAME_ONBEKEND
        kampioen.save(update_fields=['deelname'])

        # zet de competities in fase P
        zet_competitie_fase_bk_wedstrijden(data.comp18)

        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        self.e2e_check_rol('BKO')

        # zet een paar sporters op 'geen vereniging'
        self.deelnemers_no_ver = list()
        for deelnemer in self.testdata.comp18_bk_deelnemers:
            if deelnemer.volgorde == 18:
                deelnemer.bij_vereniging = None
                deelnemer.save(update_fields=['bij_vereniging'])
                self.deelnemers_no_ver.append(deelnemer)
        # for

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_bk_selectie % 999999)
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_bk_selectie_download % 999999)
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_wijzig_status % 999999)
        self.assert_is_redirect_login(resp)

    def test_selectie(self):
        # ingelogd als BKO Indoor
        resp = self.client.get(self.url_bk_selectie % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_bk_selectie % self.testdata.deelkamp25_bk.pk)
        self.assert403(resp, 'Niet de beheerder')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bk_selectie % self.testdata.deelkamp18_bk.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/bk-selectie.dtl', 'plein/site_layout.dtl'))

        # verkeerde competitie fase
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        resp = self.client.get(self.url_bk_selectie % self.testdata.deelkamp18_bk.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        self.e2e_assert_other_http_commands_not_supported(self.url_bk_selectie % 999999)

    def test_download(self):
        # ingelogd als BKO Indoor
        resp = self.client.get(self.url_bk_selectie_download % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_bk_selectie_download % self.testdata.deelkamp25_bk.pk)
        self.assert403(resp, 'Niet de beheerder')

        resp = self.client.get(self.url_bk_selectie_download % self.testdata.deelkamp18_bk.pk)
        self.assert404(resp, 'Geen deelnemerslijst')

        self.testdata.deelkamp18_bk.heeft_deelnemerslijst = True
        self.testdata.deelkamp18_bk.save(update_fields=['heeft_deelnemerslijst'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bk_selectie_download % self.testdata.deelkamp18_bk.pk)
        self.assert200_is_bestand_csv(resp)

        # repeat voor 25m1pijl
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)

        self.testdata.deelkamp25_bk.heeft_deelnemerslijst = True
        self.testdata.deelkamp25_bk.save(update_fields=['heeft_deelnemerslijst'])

        resp = self.client.get(self.url_bk_selectie_download % self.testdata.deelkamp25_bk.pk)
        self.assert200_is_bestand_csv(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_bk_selectie_download % 999999)

    def test_wijzig_status_get(self):
        # ingelogd als BKO Indoor
        resp = self.client.get(self.url_wijzig_status % 999999)
        self.assert404(resp, 'Deelnemer niet gevonden')

        deelnemer = self.testdata.comp18_bk_deelnemers[0]
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_status % deelnemer.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/wijzig-status-bk-deelnemer.dtl', 'plein/site_layout.dtl'))

        # deelnemer zonder vereniging
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_status % self.deelnemers_no_ver[0].pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/wijzig-status-bk-deelnemer.dtl', 'plein/site_layout.dtl'))

        # verkeerde competitie fase
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        resp = self.client.get(self.url_wijzig_status % deelnemer.pk)
        self.assert404(resp, 'Mag nog niet wijzigen')

        # verkeerde BKO
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        resp = self.client.get(self.url_wijzig_status % deelnemer.pk)
        self.assert403(resp, 'Niet de beheerder')

        self.e2e_assert_other_http_commands_not_supported(self.url_wijzig_status % 999999, post=False)

    def test_wijzig_status_post(self):
        # ingelogd als BKO Indoor
        resp = self.client.post(self.url_wijzig_status % 999999)
        self.assert404(resp, 'Deelnemer niet gevonden')

        deelnemer = self.testdata.comp18_bk_deelnemers[0]

        # geen data
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_status % deelnemer.pk)
        self.assert_is_redirect_not_plein(resp)

        # bevestig
        self.assertEqual(0, CompetitieMutatie.objects.count())
        resp = self.client.post(self.url_wijzig_status % deelnemer.pk, {'snel': 1, 'bevestig': '1'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, CompetitieMutatie.objects.count())

        # deelnemer zonder vereniging
        resp = self.client.post(self.url_wijzig_status % self.deelnemers_no_ver[0].pk, {'bevestig': '1'})
        self.assert404(resp, 'Sporter moet lid zijn bij een vereniging')
        self.assertEqual(1, CompetitieMutatie.objects.count())

        # afmelden
        resp = self.client.post(self.url_wijzig_status % deelnemer.pk, {'snel': 1, 'afmelden': '1'})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(2, CompetitieMutatie.objects.count())

        # verkeerde competitie fase
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        resp = self.client.post(self.url_wijzig_status % deelnemer.pk)
        self.assert404(resp, 'Mag niet meer wijzigen')

        # verkeerde BKO
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        resp = self.client.post(self.url_wijzig_status % deelnemer.pk)
        self.assert403(resp, 'Niet de beheerder')

        self.e2e_assert_other_http_commands_not_supported(self.url_wijzig_status % 999999, post=False)

# end of file
