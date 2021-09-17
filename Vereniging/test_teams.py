# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from django.utils import timezone
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import (DeelCompetitie, CompetitieKlasse, AG_NUL, LAAG_REGIO, LAAG_RK,
                               RegiocompetitieTeam, RegioCompetitieSchutterBoog, RegiocompetitieRondeTeam)
from Competitie.test_fase import zet_competitie_fase
from Competitie.test_competitie import maak_competities_en_zet_fase_b
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Schutter.models import SchutterBoog
from Score.operations import score_indiv_ag_opslaan
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime
import io


class TestVerenigingTeams(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Schutter', 'Competitie')

    url_koppelen = '/vereniging/teams/regio/koppelen/%s/'               # team_pk
    url_maak_team = '/vereniging/teams/regio/%s/nieuw/'                 # deelcomp_pk
    url_wijzig_team = '/vereniging/teams/regio/%s/wijzig/%s/'           # deelcomp_pk, team_pk
    url_regio_teams = '/vereniging/teams/regio/%s/'                     # deelcomp_pk
    url_wijzig_ag = '/vereniging/leden-ingeschreven/wijzig-aanvangsgemiddelde/%s/'  # deelnemer_pk
    url_team_invallers = '/vereniging/teams/regio/%s/invallers/'        # deelcomp_pk
    url_team_invallers_koppelen = '/vereniging/teams/regio/invallers-koppelen/%s/'  # ronde_team_pk
    url_rcl_volgende_ronde = '/bondscompetities/regio/%s/team-ronde/'   # deelcomp_pk

    url_rk_teams = '/vereniging/teams/rk/%s/'                           # deelcomp_rk_pk
    url_rk_teams_nieuw = '/vereniging/teams/rk/%s/nieuw/'               # deelcomp_rk_pk
    url_rk_teams_wijzig = '/vereniging/teams/rk/%s/wijzig/%s/'          # deelcomp_rk_pk, team_pk

    testdata = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        # secretaris kan nog niet ingevuld worden
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
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()

        self.account_hwl = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        lid.account = self.account_hwl
        lid.save()
        self.nhblid_100001 = lid

        jaar = timezone.now().year

        # maak een aspirant aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Jeugdschutter"
        lid.email = "nietleeg@nhb.not"
        lid.geboorte_datum = datetime.date(year=jaar-12, month=3, day=4)
        lid.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam)  # heeft last_login=None
        lid.save()
        self.nhblid_100002 = lid

        # maak een cadet aan
        lid = NhbLid()
        lid.nhb_nr = 100012
        lid.geslacht = "V"
        lid.voornaam = "Andrea"
        lid.achternaam = "de Jeugdschutter"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=jaar-15, month=3, day=4)
        lid.sinds_datum = datetime.date(year=jaar-3, month=10, day=10)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100012 = lid

        # maak een jeugd lid aan
        lid = NhbLid()
        lid.nhb_nr = 100004
        lid.geslacht = "M"
        lid.voornaam = "Cadet"
        lid.achternaam = "de Jeugd"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=jaar-13, month=3, day=4)    # 13=asp, maar 14 in 2e jaar competitie!
        lid.sinds_datum = datetime.date(year=jaar-3, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100004 = lid

        # maak een senior lid aan, om inactief te maken
        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=jaar-4, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100003 = lid

        # maak een senior lid aan
        lid = NhbLid()
        lid.nhb_nr = 100013
        lid.geslacht = "M"
        lid.voornaam = "Instinctive"
        lid.achternaam = "de Bower"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=5)
        lid.sinds_datum = datetime.date(year=jaar-4, month=7, day=1)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100013 = lid

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
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
        # (strategisch gekozen) historische data om klassegrenzen uit te bepalen
        histcomp = HistCompetitie()
        histcomp.seizoen = '2018/2019'
        histcomp.comp_type = '18'
        histcomp.klasse = 'Testcurve1'
        histcomp.is_team = False
        histcomp.save()

        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.schutter_nr = self.nhblid_100001.nhb_nr
        rec.schutter_naam = self.nhblid_100001.volledige_naam()
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
        rec.schutter_nr = self.nhblid_100002.nhb_nr
        rec.schutter_naam = self.nhblid_100002.volledige_naam()
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

        self.assertEqual(CompetitieKlasse.objects.count(), 0)
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_b()

        self.deelcomp18_regio111 = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                              nhb_regio=self.regio_111,
                                                              competitie__afstand=18)

        # default instellingen voor regio 111: organiseert competitie, vaste teams

        self.deelcomp25_regio111 = DeelCompetitie.objects.get(competitie=self.comp_25,
                                                              laag=LAAG_REGIO,
                                                              nhb_regio=self.regio_111)

    def _zet_schutter_voorkeuren(self, nhb_nr):
        # deze functie kan alleen gebruikt worden als HWL
        url_schutter_voorkeuren = '/sporter/voorkeuren/'

        # haal als HWL de voorkeuren pagina op van een lid van de vereniging
        # dit maakt ook de SchutterBoog records aan
        with self.assert_max_queries(20):
            resp = self.client.get(url_schutter_voorkeuren + '%s/' % nhb_nr)
        self.assertEqual(resp.status_code, 200)

        # post een wijziging
        if nhb_nr == 100003:
            with self.assert_max_queries(20):
                resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                  'schiet_BB': 'on',
                                                                  'info_R': 'on',
                                                                  'voorkeur_meedoen_competitie': 'on'})
        elif nhb_nr == 100013:
            with self.assert_max_queries(20):
                resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                  'schiet_IB': 'on',
                                                                  'voorkeur_meedoen_competitie': 'on'})
        else:
            with self.assert_max_queries(20):
                resp = self.client.post(url_schutter_voorkeuren, {'nhblid_pk': nhb_nr,
                                                                  'schiet_R': 'on',
                                                                  'info_C': 'on',
                                                                  'voorkeur_meedoen_competitie': 'on'})

        self.assert_is_redirect(resp, '/vereniging/leden-voorkeuren/')

    def _zet_ag(self, nhb_nr, afstand):
        if nhb_nr == 100003:
            afkorting = 'BB'
        elif nhb_nr == 100013:
            afkorting = 'IB'
        else:
            afkorting = 'R'
        schutterboog = SchutterBoog.objects.get(nhblid__nhb_nr=nhb_nr, boogtype__afkorting=afkorting)
        score_indiv_ag_opslaan(schutterboog, afstand, 7.42, self.account_hwl, 'Test AG %s' % afstand)

    def _create_deelnemers(self, do_18=True, do_25=False):
        # moet ingelogd zijn als HWL
        url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/'      # <comp_pk>

        self._zet_schutter_voorkeuren(100002)       # R
        self._zet_schutter_voorkeuren(100003)       # BB
        self._zet_schutter_voorkeuren(100004)       # R
        self._zet_schutter_voorkeuren(100012)       # R
        self._zet_schutter_voorkeuren(100013)       # IB

        if do_18:           # pragma: no branch
            self._zet_ag(100002, 18)
            self._zet_ag(100003, 18)
            self._zet_ag(100004, 18)
            self._zet_ag(100013, 18)

            url = url_inschrijven % self.comp_18.pk
            with self.assert_max_queries(33):
                resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',    # 1=R
                                              'lid_100003_boogtype_3': 'on',    # 3=BB
                                              'lid_100004_boogtype_1': 'on',    # 1=R
                                              'lid_100012_boogtype_1': 'on',    # 1=R
                                              'lid_100013_boogtype_4': 'on',    # 4=IB
                                              'wil_in_team': 'ja!'})
            self.assert_is_redirect_not_plein(resp)     # check success

            # print('aantal ingeschreven deelnemers:', RegioCompetitieSchutterBoog.objects.count())

            for obj in (RegioCompetitieSchutterBoog
                        .objects
                        .select_related('schutterboog__nhblid')
                        .filter(deelcompetitie__competitie=self.comp_18)
                        .all()):
                nr = obj.schutterboog.nhblid.nhb_nr
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

        if do_25:
            url = url_inschrijven % self.comp_25.pk
            with self.assert_max_queries(23):
                self.client.post(url, {'lid_100002_boogtype_1': 'on',    # 1=R
                                       'lid_100004_boogtype_1': 'on',    # 1=R
                                       'lid_100012_boogtype_1': 'on',    # 1=R
                                       'wil_in_team': 'ja!'})

            for obj in (RegioCompetitieSchutterBoog
                        .objects
                        .select_related('schutterboog__nhblid')
                        .filter(deelcompetitie__competitie=self.comp_25)
                        .all()):
                nr = obj.schutterboog.nhblid.nhb_nr
                if nr == 100002:
                    self.deelnemer_100002_25 = obj
                elif nr == 100004:
                    self.deelnemer_100004_25 = obj
                elif nr == 100012:      # pragma: no branch
                    self.deelnemer_100012_25 = obj
            # for

    def _verwerk_mutaties(self, max_mutaties=20, show=False):
        # vraag de achtergrond taak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(max_mutaties):
            management.call_command('regiocomp_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if show:                    # pragma: no coverage
            print(f1.getvalue())
            print(f2.getvalue())

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_koppelen % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_maak_team % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_wijzig_team % (999999, 999999))
        self.assert403(resp)

        resp = self.client.get(self.url_regio_teams % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_rk_teams % 999999)
        self.assert403(resp)

    def test_bad(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppelen % 999999)
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppelen % 999999)
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_maak_team % 999999)
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_team % (999999, 999999))
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (999999, 999999))
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % 999999)
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_maak_team % self.deelcomp18_regio111.pk)
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 999999))
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 999999))
        self.assert404(resp)     # 404 = Not found

        # maak een team aan zonder team_type
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0))
        self.assert404(resp)     # 404 = Not found

        # zet de competitie naar > fase E
        zet_competitie_fase(self.comp_18, 'F')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 999999))
        self.assert404(resp)     # 404 = Not found

    def test_regio_teams(self):
        # login als HWL van de vereniging in regio 111
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        zet_competitie_fase(self.comp_18, 'B')
        self.deelcomp18_regio111.einde_teams_aanmaken = self.deelcomp18_regio111.competitie.einde_aanmeldingen
        self.deelcomp18_regio111.save()

        self._create_deelnemers()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(resp.status_code, 200)

        # maak een team aan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_maak_team % self.deelcomp18_regio111.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-regio-wijzig.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(0, RegiocompetitieTeam.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                    {'team_type': 'R'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(1, RegiocompetitieTeam.objects.count())

        self.nhbver1 = NhbVereniging.objects.get(pk=self.nhbver1.pk)

        team = RegiocompetitieTeam.objects.all()[0]
        self.assertEqual(team.deelcompetitie.pk, self.deelcomp18_regio111.pk)
        self.assertEqual(team.vereniging, self.nhbver1)
        self.assertEqual(team.volg_nr, 1)
        self.assertEqual(team.team_type.afkorting, 'R')
        self.assertTrue(team.maak_team_naam() != '')
        self.assertTrue(team.maak_team_naam_kort() != '')
        self.assertTrue(str(team) != '')

        # zet het team handmatig in een klasse en koppel een schutter
        klasse = CompetitieKlasse.objects.get(competitie=self.comp_18,
                                              team__volgorde=10)           # Recurve klasse ERE
        team.klasse = klasse
        team.aanvangsgemiddelde = 8.8
        team.save()
        team.gekoppelde_schutters.add(self.deelnemer_100004_18)

        # wijzig het team type
        resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk),
                                {'team_type': 'BAD'})
        self.assert404(resp)     # 404 = Not found

        # team change
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk),
                                    {'team_type': 'C', 'team_naam': 'test test test'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

        team = RegiocompetitieTeam.objects.get(pk=team.pk)
        self.assertTrue(team.aanvangsgemiddelde < 0.0005)
        self.assertIsNone(team.klasse)
        self.assertEqual(0, team.gekoppelde_schutters.count())

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk))
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-regio-wijzig.dtl', 'plein/site_layout.dtl'))

        # no team change + name change
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk),
                                    {'team_type': 'C', 'team_naam': 'test test test'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

        # maak het maximum aantal teams aan
        for lp in range(9):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                    {'team_type': 'R'})
            self.assert_is_redirect_not_plein(resp)
        # for

        # nu zijn er 10 teams. Maak #11 aan
        resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                {'team_type': 'R'})
        self.assert404(resp)     # 404 = Not found

        # haal het teams overzicht op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-regio.dtl', 'plein/site_layout.dtl'))

        # haal het teams overzicht op voor de 25m
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.deelcomp25_regio111.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('vereniging/teams-regio.dtl', 'plein/site_layout.dtl'))

        # team = RegiocompetitieTeam.objects.all()[0]

        # voorbij einddatum aanmaken / wijzigen teams
        self.deelcomp18_regio111.einde_teams_aanmaken -= datetime.timedelta(days=5)
        self.deelcomp18_regio111.save()

        # ophalen mag, maar heeft geen wijzig / koppelen knoppen meer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('vereniging/teams-regio.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # ophalen van de wijzig-team pagina mag, maar krijgt geen opslaan knop
        url = self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-regio-wijzig.dtl', 'plein/site_layout.dtl'))

        # verwijder een team na de einddatum
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk),
                                    {'verwijderen': '1'})
        self.assert404(resp)

        # herstel de datum en verwijder het team
        self.deelcomp18_regio111.einde_teams_aanmaken = self.deelcomp18_regio111.competitie.einde_teamvorming
        self.deelcomp18_regio111.save()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk),
                                    {'verwijderen': '1'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

        # bad team pk
        resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 'notanumber'))
        self.assert404(resp)

        # nieuw team maken met bad team_type
        resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                {'team_type': 'xxx'})
        self.assert404(resp)

        # not-existing team pk
        resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 999999))
        self.assert404(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_regio_teams % self.deelcomp25_regio111.pk)

    def test_koppel(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        zet_competitie_fase(self.comp_18, 'B')
        zet_competitie_fase(self.comp_25, 'B')
        self._create_deelnemers(do_25=True)

        self.deelcomp18_regio111.einde_teams_aanmaken = self.deelcomp18_regio111.competitie.einde_aanmeldingen
        self.deelcomp18_regio111.save()

        self.deelcomp25_regio111.einde_teams_aanmaken = self.deelcomp25_regio111.competitie.einde_aanmeldingen
        self.deelcomp25_regio111.save()

        # maak een team aan
        self.assertEqual(0, RegiocompetitieTeam.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                    {'team_type': 'R'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(1, RegiocompetitieTeam.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp25_regio111.pk, 0),
                                    {'team_type': 'R'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp25_regio111.pk)
        self.assertEqual(2, RegiocompetitieTeam.objects.count())

        team_18 = RegiocompetitieTeam.objects.filter(deelcompetitie=self.deelcomp18_regio111)[0]
        team_25 = RegiocompetitieTeam.objects.filter(deelcompetitie=self.deelcomp25_regio111)[0]

        # haal de koppel pagina op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppelen % team_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-koppelen.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppelen % team_25.pk)
        self.assertEqual(resp.status_code, 200)

        # koppel leden
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppelen % team_18.pk,
                                    {'deelnemer_%s' % self.deelnemer_100002_18.pk: 1,       # aspirant
                                     'deelnemer_%s' % self.deelnemer_100003_18.pk: 1,       # BB
                                     'deelnemer_%s' % self.deelnemer_100004_18.pk: 1,
                                     'deelnemer_%s' % self.deelnemer_100012_18.pk: 1,       # geen AG
                                     'deelnemer_%s' % self.deelnemer_100004_25.pk: 1,       # verkeerde comp
                                     'deelnemer_XYZ': 1,    # geen nummer
                                     'iets_anders': 1})     # geen deelnemer parameter
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

        team_18 = RegiocompetitieTeam.objects.get(pk=team_18.pk)
        self.assertEqual(2, team_18.gekoppelde_schutters.count())
        self.assertEqual(team_18.aanvangsgemiddelde, AG_NUL)
        self.assertEqual(None, team_18.klasse)

        # koppel nog meer leden
        deelnemer = RegioCompetitieSchutterBoog.objects.get(pk=self.deelnemer_100012_18.pk)
        deelnemer.ag_voor_team = 6.500
        deelnemer.save()

        obj = CompetitieKlasse.objects.get(competitie=self.comp_18,
                                           team__volgorde=10)           # Recurve klasse ERE
        obj.min_ag = 29.5
        obj.save()

        obj = CompetitieKlasse.objects.get(competitie=self.comp_18,
                                           team__volgorde=11)           # Recurve klasse A
        obj.min_ag = 21.340     # ondergrens = precies wat het team zal hebben
        obj.save()

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppelen % team_18.pk,
                                    {'deelnemer_%s' % self.deelnemer_100003_18.pk: 1,       # BB
                                     'deelnemer_%s' % self.deelnemer_100004_18.pk: 1,
                                     'deelnemer_%s' % self.deelnemer_100012_18.pk: 1})      # geen AG
        self.assert_is_redirect_not_plein(resp)

        team_18 = RegiocompetitieTeam.objects.get(pk=team_18.pk)
        self.assertEqual(3, team_18.gekoppelde_schutters.count())
        self.assertEqual(str(team_18.aanvangsgemiddelde), '21.340')        # 7.42 + 7.42 + 6.5
        self.assertEqual(team_18.klasse, obj)

        # maak nog een team aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                    {'team_type': 'BB'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

        # haal het teams overzicht op, met gekoppelde leden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppelen % team_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-koppelen.dtl', 'plein/site_layout.dtl'))

        # haal het teams overzicht op, met geblokkeerde leden
        team_bb = RegiocompetitieTeam.objects.get(team_type__afkorting='BB')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppelen % team_bb.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('vereniging/teams-koppelen.dtl', 'plein/site_layout.dtl'))

        # koppel-scherm na uiterste datum wijzigen
        self.deelcomp18_regio111.einde_teams_aanmaken -= datetime.timedelta(days=5)
        self.deelcomp18_regio111.save()
        url = self.url_koppelen % team_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-koppelen.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post(url)
        self.assert404(resp)

    def test_wijzig_ag(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        zet_competitie_fase(self.comp_18, 'B')
        self._create_deelnemers()

        self.deelcomp18_regio111.einde_teams_aanmaken = self.deelcomp18_regio111.competitie.einde_aanmeldingen
        self.deelcomp18_regio111.save()

        # maak een team aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                    {'team_type': 'R'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(1, RegiocompetitieTeam.objects.count())
        team_18 = RegiocompetitieTeam.objects.filter(deelcompetitie=self.deelcomp18_regio111)[0]

        # haal de wijzig-ag pagina op
        url = self.url_wijzig_ag % self.deelnemer_100002_18.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-wijzig-ag.dtl', 'plein/site_layout.dtl'))

        # wijzig het AG
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': '9.876'})
        self.assert_is_redirect_not_plein(resp)

        # corner case: geen nieuw ag
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        # bad: te laag ag
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': '0.999'})
        self.assert404(resp)

        # bad: te hoog ag
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': '10.0'})
        self.assert404(resp)

        # bad code: geen float
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': 'what a big mess is this'})
        self.assert404(resp)

        # bad case: onbekende deelnemer
        bad_url = self.url_wijzig_ag % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(bad_url)
        self.assert404(resp)
        with self.assert_max_queries(20):
            resp = self.client.post(bad_url)
        self.assert404(resp)

        # bad case: lid van andere vereniging
        self.deelnemer_100002_18.bij_vereniging = self.nhbver2
        self.deelnemer_100002_18.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # nu als RCL
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # wijzig het AG
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuw_ag': '7.654'})
        self.assert_is_redirect_not_plein(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-wijzig-ag.dtl', 'plein/site_layout.dtl'))

        # verkeerde regio
        self.functie_rcl.nhb_regio = NhbRegio.objects.get(regio_nr=101)
        self.functie_rcl.save(update_fields=['nhb_regio'])
        self.e2e_wissel_naar_functie(self.functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

    def test_rk_teams(self):

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
        with self.settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=30):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelcomp_rk3.pk)
                self.assert404(resp, 'Competitie is niet in de juiste fase 2')

        # verplaats het openingstijdstip
        with self.settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=0):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelcomp_rk3.pk)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('vereniging/teams-rk.dtl', 'plein/site_layout.dtl'))

            # nieuw team aanmaken
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams_nieuw % deelcomp_rk3.pk)
                self.assertEqual(resp.status_code, 200)
                self.assert_html_ok(resp)
                self.assert_template_used(resp, ('vereniging/teams-rk-wijzig.dtl', 'plein/site_layout.dtl'))

            # maak een team aan zonder team nummer
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_rk_teams_nieuw % deelcomp_rk3.pk)
                self.assert404(resp, 'Slechte parameter')

            # maak een team aan, zonder team type
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (deelcomp_rk3.pk, 0)       # 0 = nieuw team
                resp = self.client.post(url)
                self.assert404(resp, 'Onbekend team type')

            # maak een team aan
            with self.assert_max_queries(20):
                url = self.url_rk_teams_wijzig % (deelcomp_rk3.pk, 0)  # 0 = nieuw team
                resp = self.client.post(url, {'team_type': 'R'})
                self.assert_is_redirect(resp, self.url_rk_teams % deelcomp_rk3.pk)

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
        with self.settings(COMPETITIES_OPEN_RK_TEAMS_DAYS_AFTER=0):
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_rk_teams % deelcomp_rk3.pk)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('vereniging/teams-rk.dtl', 'plein/site_layout.dtl'))

    def test_invallers(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # maak een team aan
        zet_competitie_fase(self.comp_18, 'B')
        self.deelcomp18_regio111.einde_teams_aanmaken = self.deelcomp18_regio111.competitie.einde_aanmeldingen
        self.deelcomp18_regio111.save()

        self._create_deelnemers()

        # maak een team aan
        self.assertEqual(0, RegiocompetitieTeam.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                    {'team_type': 'R'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(1, RegiocompetitieTeam.objects.count())

        self.deelnemer_100003_18.inschrijf_voorkeur_team = True
        self.deelnemer_100003_18.save(update_fields=['inschrijf_voorkeur_team'])

        self.deelnemer_100002_18.inschrijf_voorkeur_team = True
        self.deelnemer_100002_18.save(update_fields=['inschrijf_voorkeur_team'])

        team = RegiocompetitieTeam.objects.all()[0]

        # koppel leden
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppelen % team.pk,
                                    {'deelnemer_%s' % self.deelnemer_100002_18.pk: 1,       # aspirant
                                     'deelnemer_%s' % self.deelnemer_100003_18.pk: 1,       # BB
                                     'deelnemer_%s' % self.deelnemer_100004_18.pk: 1})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

        # maak nog een team aan
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 0),
                                    {'team_type': 'IB'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(2, RegiocompetitieTeam.objects.count())
        team2 = RegiocompetitieTeam.objects.exclude(pk=team.pk)[0]

        # koppel 100013 aan dit tweede team, dan is deze 'bezet' voor het 1e team
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_koppelen % team2.pk,
                                    {'deelnemer_%s' % self.deelnemer_100013_18.pk: 1})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

        # competitie in verkeerde fase
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_team_invallers % self.deelcomp18_regio111.pk)
        self.assert404(resp, 'Competitie is niet in de juiste fase')

        # zet de competitie door naar de wedstrijd fase
        zet_competitie_fase(self.comp_18, 'E')

        # verkeerde ronde nummer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_team_invallers % self.deelcomp18_regio111.pk)
        self.assert404(resp, 'Competitie ronde klopt niet')

        # wissel naar RCL
        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(self.functie_rcl)

        # zet de teamcompetitie door naar de volgende ronde
        self.assertEqual(0, RegiocompetitieRondeTeam.objects.count())
        url = self.url_rcl_volgende_ronde % self.deelcomp18_regio111.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, '/bondscompetities/%s/' % self.comp_18.pk)

        self._verwerk_mutaties(41)
        self.assertEqual(2, RegiocompetitieRondeTeam.objects.count())

        pks0 = [self.deelnemer_100002_18.pk, self.deelnemer_100003_18.pk, self.deelnemer_100004_18.pk]
        pks0.sort()
        self.assertEqual(len(pks0), 3)

        ronde_team = RegiocompetitieRondeTeam.objects.filter(team=team.pk)[0]
        pks1 = list(ronde_team.deelnemers_geselecteerd.order_by('pk').values_list('pk', flat=True))
        self.assertEqual(len(pks1), 3)
        self.assertEqual(pks0, pks1)

        pks2 = list(ronde_team.deelnemers_feitelijk.order_by('pk').values_list('pk', flat=True))
        self.assertEqual(len(pks2), 3)
        self.assertEqual(pks1, pks2)

        # wissel naar HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # haal het invallers scherm op
        url = self.url_team_invallers % self.deelcomp18_regio111.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-invallers.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url)

        # haal het koppel scherm op
        url = self.url_team_invallers_koppelen % ronde_team.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-invallers-koppelen.dtl', 'plein/site_layout.dtl'))

        # koppel een invallers
        #    noteer: 100012 heeft geen team AG
        #    print('team_ag:', self.deelnemer_100012_18.ag_voor_team)

        # originele team had maar 3 leden, dus maximaal 3 koppelen!
        # check max 3 leden in team
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'invaller_1': self.deelnemer_100002_18.pk,
                                          'invaller_2': self.deelnemer_100003_18.pk,
                                          'invaller_3': self.deelnemer_100004_18.pk,
                                          'invaller_4': self.deelnemer_100012_18.pk})
        self.assert_is_redirect(resp, self.url_team_invallers % self.deelcomp18_regio111.pk)

        ronde_team = RegiocompetitieRondeTeam.objects.get(pk=ronde_team.pk)

        pks1 = list(ronde_team.deelnemers_geselecteerd.order_by('pk').values_list('pk', flat=True))
        # sort pks1 like pks0?
        self.assertEqual(len(pks1), 3)
        self.assertEqual(pks0, pks1)

        pks2 = list(ronde_team.deelnemers_feitelijk.order_by('pk').values_list('pk', flat=True))
        # sort pks2?
        self.assertEqual(len(pks2), 3)
        self.assertEqual(pks1, pks2)

        # probeer 1 sporter drie keer te koppelen
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'invaller_1': self.deelnemer_100002_18.pk,
                                          'invaller_2': self.deelnemer_100002_18.pk,
                                          'invaller_3': self.deelnemer_100002_18.pk})
        self.assert_is_redirect(resp, self.url_team_invallers % self.deelcomp18_regio111.pk)

        pks1 = list(ronde_team.deelnemers_geselecteerd.order_by('pk').values_list('pk', flat=True))
        # sort pks1?
        self.assertEqual(len(pks1), 3)
        self.assertEqual(pks0, pks1)

        pks2 = list(ronde_team.deelnemers_feitelijk.order_by('pk').values_list('pk', flat=True))
        # sort pks2?
        self.assertEqual(len(pks2), 1)

        # pas het huidig gemiddelde van een van de originele team schutter aan
        # sporter moet toch nog te koppelen zijn
        self.deelnemer_100003_18.gemiddelde = 9.5
        self.deelnemer_100003_18.save(update_fields=['gemiddelde'])

        # voer 3 vervangers in
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'invaller_1': self.deelnemer_100003_18.pk,
                                          'invaller_2': self.deelnemer_100004_18.pk,
                                          'invaller_3': self.deelnemer_100012_18.pk})
        self.assert_is_redirect(resp, self.url_team_invallers % self.deelcomp18_regio111.pk)

        pks2 = list(ronde_team.deelnemers_feitelijk.order_by('pk').values_list('pk', flat=True))
        self.assertEqual(len(pks2), 3)

        pks3 = [self.deelnemer_100003_18.pk, self.deelnemer_100004_18.pk, self.deelnemer_100012_18.pk]
        pks3.sort()
        # sort pks2?
        self.assertEqual(pks2, pks3)

        self.deelnemer_100003_18.gemiddelde_begin_team_ronde = 9.5
        self.deelnemer_100003_18.save(update_fields=['gemiddelde_begin_team_ronde'])

        # zet te hoog gemiddelde bij de invaller
        self.deelnemer_100012_18.gemiddelde_begin_team_ronde = 9.5
        self.deelnemer_100012_18.save(update_fields=['gemiddelde_begin_team_ronde'])

        with self.assert_max_queries(20):
            self.client.post(url, {'invaller_1': self.deelnemer_100002_18.pk})

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'invaller_1': self.deelnemer_100003_18.pk,
                                          'invaller_2': self.deelnemer_100004_18.pk,
                                          'invaller_3': self.deelnemer_100012_18.pk})
        self.assert404(resp, 'Selectie is te sterk:')

        pks2 = list(ronde_team.deelnemers_feitelijk.order_by('pk').values_list('pk', flat=True))
        self.assertEqual(len(pks2), 3)

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'invaller_1': 'xx'})
        self.assert404(resp, 'Verkeerde parameters')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'invaller_1': 888888})
        self.assert404(resp, 'Geen valide selectie')

        # niet bestaande deelcomp
        resp = self.client.get(self.url_team_invallers % 999999)
        self.assert404(resp)

        # niet bestaande team-ronde
        url = self.url_team_invallers_koppelen % 999999
        resp = self.client.get(url)
        self.assert404(resp)
        resp = self.client.post(url, {})
        self.assert404(resp)

        # team zonder initiële sporters
        ronde_team.deelnemers_geselecteerd.clear()

        url = self.url_team_invallers_koppelen % ronde_team.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Team is niet compleet')


# end of file
