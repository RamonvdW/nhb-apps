# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Competitie.definities import DEEL_RK
from Competitie.models import (CompetitieIndivKlasse,
                               Regiocompetitie, RegiocompetitieSporterBoog,
                               KampioenschapTeam, Kampioenschap)
from Competitie.test_utils.tijdlijn import evaluatie_datum, zet_competitie_fase_regio_wedstrijden
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Sporter.models import Sporter, SporterBoog
from Score.operations import score_indiv_ag_opslaan
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompLaagRayonVerenigingTeams(E2EHelpers, TestCase):

    """ Tests voor de CompLaagRayon applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_rk_teams = '/bondscompetities/rk/teams-vereniging/%s/'                      # deelcomp_rk_pk
    url_rk_teams_nieuw = '/bondscompetities/rk/teams-vereniging/%s/nieuw/'          # deelcomp_rk_pk
    url_rk_teams_wijzig = '/bondscompetities/rk/teams-vereniging/%s/wijzig/%s/'     # deelcomp_rk_pk, rk_team_pk
    url_rk_teams_koppelen = '/bondscompetities/rk/teams-vereniging/koppelen/%s/'    # rk_team_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.regio_111 = Regio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio_111)
        ver.save()
        self.ver1 = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

        # maak het lid aan dat HWL wordt
        sporter = Sporter(
                        lid_nr=100001,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Tester",
                        email="rdetester@gmail.not",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver)
        sporter.save()

        self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        sporter.account = self.account_hwl
        sporter.save()
        self.sporter_100001 = sporter

        jaar = timezone.now().year

        # maak een aspirant aan
        sporter = Sporter(
                        lid_nr=100002,
                        geslacht="V",
                        voornaam="Ramona",
                        achternaam="de Jeugdschutter",
                        email="nietleeg@test.not",
                        geboorte_datum=datetime.date(year=jaar-12, month=3, day=4),
                        sinds_datum=datetime.date(year=jaar-3, month=11, day=12),
                        bij_vereniging=ver)
        # account heeft last_login=None
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()
        self.sporter_100002 = sporter

        # maak een cadet aan
        sporter = Sporter(
                        lid_nr=100012,
                        geslacht="V",
                        voornaam="Andrea",
                        achternaam="de Jeugdschutter",
                        email="",
                        geboorte_datum=datetime.date(year=jaar-15, month=3, day=4),
                        sinds_datum=datetime.date(year=jaar-3, month=10, day=10),
                        bij_vereniging=ver)
        sporter.save()
        self.sporter_100012 = sporter

        # maak een jeugd lid aan
        sporter = Sporter(
                        lid_nr=100004,
                        geslacht="M",
                        voornaam="Cadet",
                        achternaam="de Jeugd",
                        email="",
                        geboorte_datum=datetime.date(year=jaar-13, month=3, day=4),  # 14 jaar in 2e jaar competitie
                        sinds_datum=datetime.date(year=jaar-3, month=11, day=12),
                        bij_vereniging=ver)
        sporter.save()
        self.sporter_100004 = sporter

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter(
                        lid_nr=100003,
                        geslacht="V",
                        voornaam="Ramona",
                        achternaam="de Testerin",
                        email="",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=jaar-4, month=11, day=12),
                        bij_vereniging=ver)
        sporter.save()
        self.sporter_100003 = sporter

        # maak een senior lid aan
        sporter = Sporter(
                        lid_nr=100013,
                        geslacht="M",
                        voornaam="Instinctive",
                        achternaam="de Bower",
                        email="",
                        geboorte_datum=datetime.date(year=1972, month=3, day=5),
                        sinds_datum=datetime.date(year=jaar-4, month=7, day=1),
                        bij_vereniging=ver)
        sporter.save()
        self.sporter_100013 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = Vereniging(
                    naam="Andere Club",
                    ver_nr=1222,
                    regio=self.regio_111)
        ver2.save()
        self.ver2 = ver2

        self.account_rcl = self.e2e_create_account('rcl111', 'ercel@test.not', 'Ercel', accepteer_vhpg=True)
        self.functie_rcl = maak_functie('RCL Regio 111', 'RCL')
        self.functie_rcl.regio = self.ver1.regio
        self.functie_rcl.save()
        self.functie_rcl.accounts.add(self.account_rcl)

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

    def _create_histcomp(self):
        # (strategisch gekozen) historische data om klassengrenzen uit te bepalen
        hist_seizoen = HistCompSeizoen(seizoen='2018/2019', comp_type=HISTCOMP_TYPE_18,
                                       indiv_bogen=",".join(HIST_BOGEN_DEFAULT))
        hist_seizoen.save()

        # record voor het volwassen lid
        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=self.sporter_100001.lid_nr,
                    sporter_naam=self.sporter_100001.volledige_naam(),
                    vereniging_nr=self.ver1.ver_nr,
                    vereniging_naam=self.ver1.naam,
                    boogtype='R',
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=70,
                    totaal=80,
                    gemiddelde=5.321)
        rec.save()

        # record voor het jeugdlid
        # record voor het volwassen lid
        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=self.sporter_100002.lid_nr,
                    sporter_naam=self.sporter_100002.volledige_naam(),
                    vereniging_nr=self.ver1.ver_nr,
                    vereniging_naam=self.ver1.naam,
                    boogtype='BB',
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=70,
                    totaal=80,
                    gemiddelde=5.321)
        rec.save()

    def _create_competitie(self):
        # BB worden
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.assertEqual(CompetitieIndivKlasse.objects.count(), 0)
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_c()

        self.deelcomp18_regio111 = Regiocompetitie.objects.get(regio=self.regio_111,
                                                               competitie__afstand=18)

        # default instellingen voor regio 111: organiseert competitie, vaste teams

        self.deelcomp25_regio111 = Regiocompetitie.objects.get(competitie=self.comp_25,
                                                               regio=self.regio_111)

    def _zet_schutter_voorkeuren(self, lid_nr):
        # deze functie kan alleen gebruikt worden als HWL
        url_sporter_voorkeuren = '/sporter/voorkeuren/'

        # maak de SporterBoog aan
        if lid_nr == 100003:
            resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_BB': 'on',
                                                             'info_R': 'on',
                                                             'voorkeur_meedoen_competitie': 'on'})
        elif lid_nr == 100013:
            resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_TR': 'on',
                                                             'voorkeur_meedoen_competitie': 'on'})
        else:
            resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_R': 'on',
                                                             'info_C': 'on',
                                                             'voorkeur_meedoen_competitie': 'on'})

        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

    def _zet_ag(self, lid_nr, afstand):
        if lid_nr == 100003:
            afkorting = 'BB'
        elif lid_nr == 100013:
            afkorting = 'TR'
        else:
            afkorting = 'R'
        sporterboog = SporterBoog.objects.get(sporter__lid_nr=lid_nr, boogtype__afkorting=afkorting)
        score_indiv_ag_opslaan(sporterboog, afstand, 7.42, self.account_hwl, 'Test AG %s' % afstand)

    def _create_deelnemers(self):
        # moet ingelogd zijn als HWL
        url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/'      # <comp_pk>

        self._zet_schutter_voorkeuren(100002)       # R
        self._zet_schutter_voorkeuren(100003)       # BB
        self._zet_schutter_voorkeuren(100004)       # R
        self._zet_schutter_voorkeuren(100012)       # R
        self._zet_schutter_voorkeuren(100013)       # TR

        self._zet_ag(100002, 18)
        self._zet_ag(100003, 18)
        self._zet_ag(100004, 18)
        self._zet_ag(100013, 18)

        url = url_inschrijven % self.comp_18.pk
        with self.assert_max_queries(43):
            # TODO: vervangen boogtype pk met afkorting!
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',    # 1=R
                                          'lid_100003_boogtype_3': 'on',    # 3=BB
                                          'lid_100004_boogtype_1': 'on',    # 1=R
                                          'lid_100012_boogtype_1': 'on',    # 1=R
                                          'lid_100013_boogtype_6': 'on',    # 6=TR
                                          'wil_in_team': 'ja!'})
        self.assert_is_redirect_not_plein(resp)     # check success

        # print('aantal ingeschreven deelnemers:', RegioCompetitieSporterBoog.objects.count())

        for obj in (RegiocompetitieSporterBoog
                    .objects
                    .select_related('sporterboog__sporter')
                    .filter(regiocompetitie__competitie=self.comp_18)
                    .all()):
            nr = obj.sporterboog.sporter.lid_nr
            if nr == 100002:
                self.deelnemer_100002_18 = obj
            elif nr == 100003:
                self.deelnemer_100003_18 = obj
            elif nr == 100004:
                self.deelnemer_100004_18 = obj
            elif nr == 100012:
                self.deelnemer_100012_18 = obj
            elif nr == 100013:  # pragma: no branch
                self.deelnemer_100013_18 = obj
        # for

    def test_rk_teams(self):
        self.client.logout()
        resp = self.client.get(self.url_rk_teams % 999999)
        self.assert403(resp)

        # login als HWL van vereniging 1000 in regio 111
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        deelkamp_rk3 = (Kampioenschap
                        .objects
                        .get(competitie=self.comp_18,
                             deel=DEEL_RK,
                             rayon__rayon_nr=3))     # regio 111 is in rayon 3

        # competitie in de verkeerde fase
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_rk_teams % deelkamp_rk3.pk)
            self.assert404(resp, 'Competitie is niet in de juiste fase 1')

        # zet competitie in fase F
        evaluatie_datum.zet_test_datum('')
        zet_competitie_fase_regio_wedstrijden(self.comp_18)

        # competitie in de verkeerde fase
        with override_settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=30):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelkamp_rk3.pk)
                self.assert404(resp, 'Competitie is niet in de juiste fase 2')

        # verplaats het openingstijdstip
        with override_settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=0):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelkamp_rk3.pk)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams.dtl', 'plein/site_layout.dtl'))

            # team aanmaken pagina
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams_nieuw % deelkamp_rk3.pk)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams-wijzig.dtl', 'plein/site_layout.dtl'))

            # maak een team aan zonder team nummer
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_rk_teams_nieuw % deelkamp_rk3.pk)
                self.assert404(resp, 'Slechte parameter')

            # bad deelcomp_pk
            url = self.url_rk_teams_wijzig % (999999, 0)
            resp = self.client.get(url)
            self.assert404(resp, 'Kampioenschap niet gevonden')

            # maak een team aan, zonder team type
            url = self.url_rk_teams_wijzig % (deelkamp_rk3.pk, 0)  # 0 = nieuw team
            with self.assert_max_queries(20):
                resp = self.client.post(url)
                self.assert404(resp, 'Onbekend team type')

            # maak een team aan
            self.assertEqual(KampioenschapTeam.objects.count(), 0)
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (deelkamp_rk3.pk, 0)  # 0 = nieuw team
                resp = self.client.post(url, {'team_type': 'R2'})
                self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'
            self.assertEqual(KampioenschapTeam.objects.count(), 1)

            team = KampioenschapTeam.objects.first()

            # coverage
            self.assertTrue(str(team) != "")

            # wijzig een team
            url = self.url_rk_teams_wijzig % (deelkamp_rk3.pk, team.pk)
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams-wijzig.dtl', 'plein/site_layout.dtl'))

            # team does not exist
            resp = self.client.get(self.url_rk_teams_wijzig % (deelkamp_rk3.pk, 999999))
            self.assert404(resp, 'Team niet gevonden of niet van jouw vereniging')

            resp = self.client.post(self.url_rk_teams_wijzig % (deelkamp_rk3.pk, 999999), {})
            self.assert404(resp, 'Team bestaat niet')

            # wijzig team type
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'team_type': 'C'})
            self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'

            # verwijder een team
            url = self.url_rk_teams_wijzig % (deelkamp_rk3.pk, team.pk)
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'verwijderen': 1})
            self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'

        # with

        # niet bestaande deelcomp_rk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_rk_teams % self.deelcomp18_regio111.pk)
            self.assert404(resp, 'Kampioenschap niet gevonden')

        # repeat voor de 25m
        deelkamp_rk3 = (Kampioenschap
                        .objects
                        .get(competitie=self.comp_25,
                             deel=DEEL_RK,
                             rayon__rayon_nr=3))     # regio 111 is in rayon 3

        # zet competitie in fase E
        zet_competitie_fase_regio_wedstrijden(self.comp_25)

        # verplaats het openingstijdstip
        with override_settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=0):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelkamp_rk3.pk)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams.dtl', 'plein/site_layout.dtl'))

    def test_rk_teams_koppelen(self):

        # login als HWL van vereniging 1000 in regio 111
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        self._create_deelnemers()

        deelkamp_rk3 = (Kampioenschap
                        .objects
                        .get(competitie=self.comp_18,
                             deel=DEEL_RK,
                             rayon__rayon_nr=3))     # regio 111 is in rayon 3

        # zet competitie in fase F (nodig om een team aan te maken)
        zet_competitie_fase_regio_wedstrijden(self.comp_18)

        with override_settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=0):
            # maak een team aan
            self.assertEqual(KampioenschapTeam.objects.count(), 0)
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (deelkamp_rk3.pk, 0)  # 0 = nieuw team
                resp = self.client.post(url, {'team_type': 'R2'})
                self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'
            self.assertEqual(KampioenschapTeam.objects.count(), 1)

            team = KampioenschapTeam.objects.first()
            url = self.url_rk_teams_koppelen % team.pk

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams-koppelen.dtl', 'plein/site_layout.dtl'))

            resp = self.client.post(url, {'deelnemer_999999': 1, 'deelnemer_xyz': 1})
            self.assert_is_redirect_not_plein(resp)

            # bad team pk
            resp = self.client.get(self.url_rk_teams_koppelen % 999999)
            self.assert404(resp, 'Team niet gevonden')

            resp = self.client.post(self.url_rk_teams_koppelen % 999999)
            self.assert404(resp, 'Team niet gevonden')

            # herhaal voor 25m1p
            deelkamp_rk3 = (Kampioenschap
                            .objects
                            .get(competitie=self.comp_25,
                                 deel=DEEL_RK,
                                 rayon__rayon_nr=3))     # regio 111 is in rayon 3

            # zet competitie in fase E (nodig om een team aan te maken)
            zet_competitie_fase_regio_wedstrijden(self.comp_25)

            # maak een team aan
            team.delete()
            self.assertEqual(KampioenschapTeam.objects.count(), 0)
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (deelkamp_rk3.pk, 0)  # 0 = nieuw team
                resp = self.client.post(url, {'team_type': 'R2'})
                self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'
            self.assertEqual(KampioenschapTeam.objects.count(), 1)

            team = KampioenschapTeam.objects.first()
            url = self.url_rk_teams_koppelen % team.pk

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams-koppelen.dtl', 'plein/site_layout.dtl'))

# end of file
