# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Competitie.models import (DeelCompetitie, CompetitieIndivKlasse, LAAG_REGIO, LAAG_RK,
                               RegioCompetitieSchutterBoog, KampioenschapTeam)
from Competitie.tests.test_fase import zet_competitie_fase
from Competitie.tests.test_competitie import maak_competities_en_zet_fase_b
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Sporter.models import Sporter, SporterBoog
from Score.operations import score_indiv_ag_opslaan
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompLaagRayonVerenigingTeams(E2EHelpers, TestCase):

    """ Tests voor de CompLaagRayon applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_rk_teams = '/bondscompetities/rk/teams-vereniging/%s/'                      # deelcomp_rk_pk
    url_rk_teams_nieuw = '/bondscompetities/rk/teams-vereniging/%s/nieuw/'          # deelcomp_rk_pk
    url_rk_teams_wijzig = '/bondscompetities/rk/teams-vereniging/%s/wijzig/%s/'     # deelcomp_rk_pk, rk_team_pk
    url_rk_teams_koppelen = '/bondscompetities/rk/teams-vereniging/koppelen/%s/'    # rk_team_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_111
        ver.save()
        self.nhbver1 = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak het lid aan dat HWL wordt
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = "rdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

        self.account_hwl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        sporter.account = self.account_hwl
        sporter.save()
        self.sporter_100001 = sporter

        jaar = timezone.now().year

        # maak een aspirant aan
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Jeugdschutter"
        sporter.email = "nietleeg@nhb.not"
        sporter.geboorte_datum = datetime.date(year=jaar-12, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)  # heeft last_login=None
        sporter.save()
        self.sporter_100002 = sporter

        # maak een cadet aan
        sporter = Sporter()
        sporter.lid_nr = 100012
        sporter.geslacht = "V"
        sporter.voornaam = "Andrea"
        sporter.achternaam = "de Jeugdschutter"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=jaar-15, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=jaar-3, month=10, day=10)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100012 = sporter

        # maak een jeugd lid aan
        sporter = Sporter()
        sporter.lid_nr = 100004
        sporter.geslacht = "M"
        sporter.voornaam = "Cadet"
        sporter.achternaam = "de Jeugd"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=jaar-13, month=3, day=4)    # 13=asp, maar 14 in 2e jaar competitie!
        sporter.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100004 = sporter

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "V"
        sporter.voornaam = "Ramona"
        sporter.achternaam = "de Testerin"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100003 = sporter

        # maak een senior lid aan
        sporter = Sporter()
        sporter.lid_nr = 100013
        sporter.geslacht = "M"
        sporter.voornaam = "Instinctive"
        sporter.achternaam = "de Bower"
        sporter.email = ""
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=5)
        sporter.sinds_datum = datetime.date(year=jaar-4, month=7, day=1)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100013 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = self.regio_111
        ver2.save()
        self.nhbver2 = ver2

        self.account_rcl = self.e2e_create_account('rcl111', 'ercel@nhb.not', 'Ercel', accepteer_vhpg=True)
        self.functie_rcl = maak_functie('RCL Regio 111', 'RCL')
        self.functie_rcl.nhb_regio = self.nhbver1.regio
        self.functie_rcl.save()
        self.functie_rcl.accounts.add(self.account_rcl)

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

    def _create_histcomp(self):
        # (strategisch gekozen) historische data om klassengrenzen uit te bepalen
        histcomp = HistCompetitie()
        histcomp.seizoen = '2018/2019'
        histcomp.comp_type = '18'
        histcomp.boog_str = 'Testcurve1'
        histcomp.is_team = False
        histcomp.save()

        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.sporter_lid_nr = self.sporter_100001.lid_nr
        rec.sporter_naam = self.sporter_100001.volledige_naam()
        rec.vereniging_nr = self.nhbver1.ver_nr
        rec.vereniging_naam = self.nhbver1.naam
        rec.boogtype = 'R'
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()

        # record voor het jeugdlid
        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.sporter_lid_nr = self.sporter_100002.lid_nr
        rec.sporter_naam = self.sporter_100002.volledige_naam()
        rec.vereniging_nr = self.nhbver1.ver_nr
        rec.vereniging_naam = self.nhbver1.naam
        rec.boogtype = 'BB'
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()

    def _create_competitie(self):
        # BB worden
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.assertEqual(CompetitieIndivKlasse.objects.count(), 0)
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_b()

        self.deelcomp18_regio111 = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                              nhb_regio=self.regio_111,
                                                              competitie__afstand=18)

        # default instellingen voor regio 111: organiseert competitie, vaste teams

        self.deelcomp25_regio111 = DeelCompetitie.objects.get(competitie=self.comp_25,
                                                              laag=LAAG_REGIO,
                                                              nhb_regio=self.regio_111)

    def _zet_schutter_voorkeuren(self, lid_nr):
        # deze functie kan alleen gebruikt worden als HWL
        url_sporter_voorkeuren = '/sporter/voorkeuren/'

        # haal als HWL de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SporterBoog records aan
        with self.assert_max_queries(20):
            resp = self.client.get(url_sporter_voorkeuren + '%s/' % lid_nr)
        self.assertEqual(resp.status_code, 200)

        # post een wijziging
        if lid_nr == 100003:
            with self.assert_max_queries(23):
                resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_BB': 'on',
                                                                 'info_R': 'on',
                                                                 'voorkeur_meedoen_competitie': 'on'})
        elif lid_nr == 100013:
            with self.assert_max_queries(24):
                resp = self.client.post(url_sporter_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_TR': 'on',
                                                                 'voorkeur_meedoen_competitie': 'on'})
        else:
            with self.assert_max_queries(23):
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
            resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',    # 1=R       # TODO: vervangen boogtype pk met afkorting!
                                          'lid_100003_boogtype_3': 'on',    # 3=BB
                                          'lid_100004_boogtype_1': 'on',    # 1=R
                                          'lid_100012_boogtype_1': 'on',    # 1=R
                                          'lid_100013_boogtype_6': 'on',    # 6=TR
                                          'wil_in_team': 'ja!'})
        self.assert_is_redirect_not_plein(resp)     # check success

        # print('aantal ingeschreven deelnemers:', RegioCompetitieSchutterBoog.objects.count())

        for obj in (RegioCompetitieSchutterBoog
                    .objects
                    .select_related('sporterboog__sporter')
                    .filter(deelcompetitie__competitie=self.comp_18)
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

        deelcomp_rk3 = (DeelCompetitie
                        .objects
                        .get(competitie=self.comp_18,
                             laag=LAAG_RK,
                             nhb_rayon__rayon_nr=3))     # regio 111 is in rayon 3

        # competitie in de verkeerde fase
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_rk_teams % deelcomp_rk3.pk)
            self.assert404(resp, 'Competitie is niet in de juiste fase 1')

        # zet competitie in fase E
        zet_competitie_fase(self.comp_18, 'E')

        # competitie in de verkeerde fase
        with override_settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=30):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelcomp_rk3.pk)
                self.assert404(resp, 'Competitie is niet in de juiste fase 2')

        # verplaats het openingstijdstip
        with override_settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=0):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelcomp_rk3.pk)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams.dtl', 'plein/site_layout.dtl'))

            # team aanmaken pagina
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams_nieuw % deelcomp_rk3.pk)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams-wijzig.dtl', 'plein/site_layout.dtl'))

            # maak een team aan zonder team nummer
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_rk_teams_nieuw % deelcomp_rk3.pk)
                self.assert404(resp, 'Slechte parameter')

            # bad deelcomp_pk
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (999999, 0)
                resp = self.client.get(url)
                self.assert404(resp, 'Competitie niet gevonden')

            # maak een team aan, zonder team type
            url = self.url_rk_teams_wijzig % (deelcomp_rk3.pk, 0)  # 0 = nieuw team
            with self.assert_max_queries(20):
                resp = self.client.post(url)
                self.assert404(resp, 'Onbekend team type')

            # maak een team aan
            self.assertEqual(KampioenschapTeam.objects.count(), 0)
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (deelcomp_rk3.pk, 0)  # 0 = nieuw team
                resp = self.client.post(url, {'team_type': 'R2'})
                self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'
            self.assertEqual(KampioenschapTeam.objects.count(), 1)

            team = KampioenschapTeam.objects.all()[0]

            # coverage
            self.assertTrue(str(team) != "")

            # wijzig een team
            url = self.url_rk_teams_wijzig % (deelcomp_rk3.pk, team.pk)
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams-wijzig.dtl', 'plein/site_layout.dtl'))

            # team does not exist
            resp = self.client.get(self.url_rk_teams_wijzig % (deelcomp_rk3.pk, 999999))
            self.assert404(resp, 'Team niet gevonden of niet van jouw vereniging')

            resp = self.client.post(self.url_rk_teams_wijzig % (deelcomp_rk3.pk, 999999), {})
            self.assert404(resp, 'Team bestaat niet')

            # wijzig team type
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'team_type': 'C'})
            self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'

            # verwijder een team
            url = self.url_rk_teams_wijzig % (deelcomp_rk3.pk, team.pk)
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'verwijderen': 1})
            self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'

        # with

        # niet bestaande deelcomp_rk
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_rk_teams % self.deelcomp18_regio111.pk)
            self.assert404(resp, 'Competitie niet gevonden')

        # repeat voor de 25m
        deelcomp_rk3 = (DeelCompetitie
                        .objects
                        .get(competitie=self.comp_25,
                             laag=LAAG_RK,
                             nhb_rayon__rayon_nr=3))     # regio 111 is in rayon 3

        # zet competitie in fase E
        zet_competitie_fase(self.comp_25, 'E')

        # verplaats het openingstijdstip
        with override_settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=0):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelcomp_rk3.pk)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams.dtl', 'plein/site_layout.dtl'))

    def test_rk_teams_koppelen(self):

        # login als HWL van vereniging 1000 in regio 111
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        self._create_deelnemers()

        deelcomp_rk3 = (DeelCompetitie
                        .objects
                        .get(competitie=self.comp_18,
                             laag=LAAG_RK,
                             nhb_rayon__rayon_nr=3))     # regio 111 is in rayon 3

        # zet competitie in fase E (nodig om een team aan te maken)
        zet_competitie_fase(self.comp_18, 'E')

        with override_settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=0):
            # maak een team aan
            self.assertEqual(KampioenschapTeam.objects.count(), 0)
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (deelcomp_rk3.pk, 0)  # 0 = nieuw team
                resp = self.client.post(url, {'team_type': 'R2'})
                self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'
            self.assertEqual(KampioenschapTeam.objects.count(), 1)

            team = KampioenschapTeam.objects.all()[0]
            url = self.url_rk_teams_koppelen % team.pk

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams-koppelen.dtl', 'plein/site_layout.dtl'))

            with self.assert_max_queries(20):
                resp = self.client.post(url, {'deelnemer_999999': 1, 'deelnemer_xyz': 1})
            self.assert_is_redirect_not_plein(resp)

            # bad team pk
            resp = self.client.get(self.url_rk_teams_koppelen % 999999)
            self.assert404(resp, 'Team niet gevonden')

            resp = self.client.post(self.url_rk_teams_koppelen % 999999)
            self.assert404(resp, 'Team niet gevonden')

            # herhaal voor 25m1p
            deelcomp_rk3 = (DeelCompetitie
                            .objects
                            .get(competitie=self.comp_25,
                                 laag=LAAG_RK,
                                 nhb_rayon__rayon_nr=3))     # regio 111 is in rayon 3

            # zet competitie in fase E (nodig om een team aan te maken)
            zet_competitie_fase(self.comp_25, 'E')

            # maak een team aan
            team.delete()
            self.assertEqual(KampioenschapTeam.objects.count(), 0)
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (deelcomp_rk3.pk, 0)  # 0 = nieuw team
                resp = self.client.post(url, {'team_type': 'R2'})
                self.assert_is_redirect_not_plein(resp)     # is redirect naar 'koppelen'
            self.assertEqual(KampioenschapTeam.objects.count(), 1)

            team = KampioenschapTeam.objects.all()[0]
            url = self.url_rk_teams_koppelen % team.pk

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('complaagrayon/hwl-teams-koppelen.dtl', 'plein/site_layout.dtl'))

# end of file
