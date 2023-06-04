# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.definities import DEELNAME_ONBEKEND
from Competitie.models import CompetitieMatch, KampioenschapIndivKlasseLimiet, KampioenschapSporterBoog
from Competitie.tijdlijn import zet_competitie_fase_bk_wedstrijden, zet_competitie_fase_rk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Wedstrijden.models import WedstrijdLocatie


class TestCompLaagBondIndiv(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, Indiv views """

    test_after = ('Competitie.tests.test_overzicht', 'CompBeheer.tests.test_bko')

    url_bk_selectie = '/bondscompetities/bk/selectie/%s/'                               # deelkamp_pk
    url_bk_selectie_download = '/bondscompetities/bk/selectie/%s/bestand/'              # deelkamp_pk
    url_wijzig_status = '/bondscompetities/bk/selectie/wijzig-status-bk-deelnemer/%s/'  # deelnemer_pk

    url_forms_indiv = '/bondscompetities/bk/formulieren/indiv/%s/'               # deelkamp_bk
    url_forms_teams = '/bondscompetities/bk/formulieren/teams/%s/'               # deelkamp_bk
    url_forms_download_indiv = '/bondscompetities/bk/formulieren/indiv/download/%s/%s/'   # match_pk, klasse_pk
    url_forms_download_teams = '/bondscompetities/bk/formulieren/teams/download/%s/%s/'   # match_pk, klasse_pk

    testdata = None
    bk18_pk = 0

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
            data.maak_uitslag_rk_indiv(18)
            data.maak_bk_deelnemers(18, ver_nr, limit_boogtypen=['R', 'BB'])
            data.maak_bk_teams(18)
        # for

        # we hebben heel veel sporters in Recurve klasse 6
        # (waarschijnlijk omdat de klassegrenzen niet vastgesteld zijn)
        grote_klasse = KampioenschapSporterBoog.objects.filter(kampioenschap=data.deelkamp18_bk, volgorde=20)[0].indiv_klasse
        KampioenschapIndivKlasseLimiet(kampioenschap=data.deelkamp18_bk, indiv_klasse=grote_klasse, limiet=8).save()

        # zet een paar sporters op 'geen vereniging'
        KampioenschapSporterBoog.objects.filter(volgorde=18).update(bij_vereniging=None)

        # zet een sporter met kampioen label op 'deelname onzeker'
        kampioen = KampioenschapSporterBoog.objects.exclude(kampioen_label='').order_by('pk')[0]
        kampioen.deelname = DEELNAME_ONBEKEND
        kampioen.save(update_fields=['deelname'])

        # zet de competities in fase P
        zet_competitie_fase_bk_wedstrijden(data.comp18)

        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %s seconds' % (cls.__name__, d.seconds))

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        self.e2e_check_rol('BKO')

        # from Competitie.models import Competitie
        # comp = Competitie.objects.get(pk=self.testdata.comp18.pk)
        # comp.bepaal_fase()
        # print('fase:', comp.fase_indiv, comp.fase_teams)

        return

        loc = WedstrijdLocatie(banen_18m=8,
                               banen_25m=8,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(self.ver)

        # maak een BK wedstrijd aan
        self.match = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='test wedstrijd BK',
                        datum_wanneer='2020-01-01',
                        tijd_begin_wedstrijd='10:00',
                        vereniging=self.ver,              # koppelt wedstrijd aan de vereniging
                        locatie=loc)
        self.match.save()

        # koppel de wedstrijdklassen aan de match
        match_klassen = list()
        for klasse in self.testdata.comp18_klassen_indiv['R']:
            if klasse.is_ook_voor_rk_bk:
                match_klassen.append(klasse)
        # for
        self.match.indiv_klassen.add(*match_klassen)
        self.comp18_klassen_indiv_bk = match_klassen

        match_klassen = list()
        for klasse in self.testdata.comp18_klassen_teams['R2']:
            match_klassen.append(klasse)
        # for
        self.match.team_klassen.add(*match_klassen)
        self.comp18_klassen_teams_bk = match_klassen

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

        resp = self.client.get(self.url_bk_selectie % self.testdata.deelkamp18_bk.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/bk-selectie.dtl', 'plein/site_layout.dtl'))

        # verkeerde competitie fase
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        resp = self.client.get(self.url_bk_selectie % self.testdata.deelkamp18_bk.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        self.e2e_assert_other_http_commands_not_supported(self.url_bk_selectie)

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

        resp = self.client.get(self.url_bk_selectie_download % self.testdata.deelkamp18_bk.pk)
        self.assert200_is_bestand_csv(resp)

        # repeat voor 25m1pijl
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)

        self.testdata.deelkamp25_bk.heeft_deelnemerslijst = True
        self.testdata.deelkamp25_bk.save(update_fields=['heeft_deelnemerslijst'])

        resp = self.client.get(self.url_bk_selectie_download % self.testdata.deelkamp25_bk.pk)
        self.assert200_is_bestand_csv(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_bk_selectie_download)

    def test_wijzig_status(self):
        # ingelogd als BKO Indoor
        resp = self.client.get(self.url_wijzig_status % 999999)
        self.assert404(resp, 'Deelnemer niet gevonden')

        #resp = self.client.get(self.url_wijzig_status % 0)      # TODO

        self.e2e_assert_other_http_commands_not_supported(self.url_bk_selectie_download, post=False)

# end of file
