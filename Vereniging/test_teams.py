# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import (Competitie, DeelCompetitie, CompetitieKlasse, AG_NUL,
                               RegiocompetitieTeam, LAAG_REGIO, RegioCompetitieSchutterBoog)
from Competitie.test_fase import zet_competitie_fase
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Schutter.models import SchutterBoog
from Score.models import score_indiv_ag_opslaan
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestVerenigingTeams(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Schutter', 'Competitie')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een BB aan, nodig om de competitie aan te maken
        self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

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

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()
        self.nhbver2 = ver2

        # maak de competitie aan die nodig is voor deze tests
        self._create_histcomp()
        self._create_competitie()

        self.url_koppelen = '/vereniging/teams/regio/koppelen/%s/'      # team_pk
        self.url_maak_team = '/vereniging/teams/regio/%s/nieuw/'        # deelcomp_pk
        self.url_wijzig_team = '/vereniging/teams/regio/%s/wijzig/%s/'  # deelcomp_pk, team_pk
        self.url_regio_teams = '/vereniging/teams/regio/%s/'            # deelcomp_pk
        self.url_rk_teams = '/vereniging/teams/rk/%s/'                  # deelcomp_pk

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
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        url_kies = '/bondscompetities/'
        url_aanmaken = '/bondscompetities/aanmaken/'
        url_klassegrenzen = '/bondscompetities/%s/klassegrenzen/vaststellen/'   # comp_pk

        self.assertEqual(CompetitieKlasse.objects.count(), 0)

        # competitie aanmaken
        with self.assert_max_queries(20):
            resp = self.client.post(url_aanmaken)
        self.assert_is_redirect(resp, url_kies)

        self.comp_18 = Competitie.objects.get(afstand=18)
        self.comp_25 = Competitie.objects.get(afstand=25)

        # klassegrenzen vaststellen
        with self.assert_max_queries(24):
            resp = self.client.post(url_klassegrenzen % self.comp_18.pk)
        self.assert_is_redirect(resp, url_kies)
        with self.assert_max_queries(24):
            resp = self.client.post(url_klassegrenzen % self.comp_25.pk)
        self.assert_is_redirect(resp, url_kies)

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

        if do_18:
            self._zet_ag(100002, 18)
            self._zet_ag(100003, 18)
            self._zet_ag(100004, 18)

            url = url_inschrijven % self.comp_18.pk
            with self.assert_max_queries(38):
                resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',    # 1=R
                                              'lid_100003_boogtype_3': 'on',    # 3=BB
                                              'lid_100004_boogtype_1': 'on',    # 1=R
                                              'lid_100012_boogtype_1': 'on',    # 1=R
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
            # for

        if do_25:
            url = url_inschrijven % self.comp_25.pk
            with self.assert_max_queries(38):
                resp = self.client.post(url, {'lid_100002_boogtype_1': 'on',    # 1=R
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
                elif nr == 100012:
                    self.deelnemer_100012_25 = obj
            # for

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

        # zet de competitie naar fase > C
        zet_competitie_fase(self.comp_18, 'D')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assert404(resp)     # 404 = Not found

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_team % (self.deelcomp18_regio111.pk, 999999))
        self.assert404(resp)     # 404 = Not found

    def test_regio_teams(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        zet_competitie_fase(self.comp_18, 'B')
        self._create_deelnemers()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.deelcomp18_regio111.pk)
        self.assertEqual(resp.status_code, 200)

        # maak een team aan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_maak_team % self.deelcomp18_regio111.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

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

        # wijzig het team type
        resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk),
                                {'team_type': 'BAD'})
        self.assert404(resp)     # 404 = Not found

        # team change
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk),
                                    {'team_type': 'C', 'team_naam': 'test test test'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

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
        self.assert_template_used(resp, ('vereniging/teams-regio.dtl', 'plein/site_layout.dtl'))

        # haal het teams overzicht op voor de 25m
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_regio_teams % self.deelcomp25_regio111.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('vereniging/teams-regio.dtl', 'plein/site_layout.dtl'))

        # verwijder een team
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_team % (self.deelcomp18_regio111.pk, team.pk),
                                    {'verwijderen': '1'})
        self.assert_is_redirect(resp, self.url_regio_teams % self.deelcomp18_regio111.pk)

    def test_koppel(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        zet_competitie_fase(self.comp_18, 'B')
        zet_competitie_fase(self.comp_25, 'B')
        self._create_deelnemers(do_25=True)

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
        self.assert_template_used(resp, ('vereniging/teams-koppelen.dtl', 'plein/site_layout.dtl'))

        # haal het teams overzicht op, met geblokkeerde leden
        team_bb = RegiocompetitieTeam.objects.get(team_type__afkorting='BB')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_koppelen % team_bb.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('vereniging/teams-koppelen.dtl', 'plein/site_layout.dtl'))

    def test_rk_teams(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_rk_teams % 999999)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/teams-rk.dtl', 'plein/site_layout.dtl'))


# end of file
