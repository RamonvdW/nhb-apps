# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.definities import INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3
from Competitie.models import (CompetitieIndivKlasse, CompetitieMatch,
                               Regiocompetitie, RegiocompetitieSporterBoog, RegiocompetitieRonde)
from Competitie.test_utils.tijdlijn import zet_competitie_fases
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from Functie.models import Functie
from Geo.models import Regio
from Score.definities import AG_DOEL_INDIV
from Score.models import Aanvangsgemiddelde, AanvangsgemiddeldeHist
from Score.operations import score_indiv_ag_opslaan, score_teams_ag_opslaan
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from time import sleep
import datetime


class TestCompInschrijvenSporter(E2EHelpers, TestCase):

    """ tests voor de CompInschrijven applicatie; module Aanmelden/Afmelden sporter """

    test_after = ('Account', 'ImportCRM', 'Competitie')

    url_profiel = '/sporter/'
    url_voorkeuren = '/sporter/voorkeuren/'
    url_aanmelden = '/bondscompetities/deelnemen/aanmelden/%s/%s/'                     # deelcomp_pk, sporterboog_pk
    url_bevestig_aanmelden = '/bondscompetities/deelnemen/aanmelden/%s/%s/bevestig/'   # deelcomp_pk, sporterboog_pk
    url_afmelden = '/bondscompetities/deelnemen/afmelden/%s/'                          # regiocomp_pk
    url_zeven_wedstrijden = '/bondscompetities/regio/keuze-zeven-wedstrijden/%s/'      # deelnemer_pk
    url_planning_regio = '/bondscompetities/regio/planning/%s/'                        # deelcomp_pk
    url_planning_regio_ronde_methode1 = '/bondscompetities/regio/planning/regio-wedstrijden/%s/'  # ronde_pk
    url_wijzig_wedstrijd = '/bondscompetities/regio/planning/wedstrijd/wijzig/%s/'     # match_pk
    url_inschrijven_hwl = '/bondscompetities/deelnemen/leden-aanmelden//%s/'           # comp_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_geen_lid = self.e2e_create_account('geen_lid', 'geenlid@test.com', 'Geen')
        self.account_twee = self.e2e_create_account('twee', 'twee@test.com', 'Twee')

        # afhankelijk van het rayon / de regios aangemaakt door NhbStructuur migratie

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver = ver

        # maak een test lid aan
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_normaal,
                    email=self.account_normaal.email)
        sporter.save()
        self.sporter1 = sporter

        # maak een test lid aan
        sporter = Sporter(
                        lid_nr=100002,
                        geslacht="V",
                        voornaam="Twee",
                        achternaam="de Tester",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver,
                        account=self.account_twee,
                        email=self.account_twee.email)
        sporter.save()

        # maak een test lid aan
        sporter = Sporter(
                        lid_nr=100003,
                        geslacht="V",
                        voornaam="Geen",
                        achternaam="Lid",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        account=self.account_geen_lid,
                        email=self.account_geen_lid.email)
        sporter.save()

    def _prep_voorkeuren(self, lid_nr):
        # zet de bogen 'aan'
        resp = self.client.post(self.url_voorkeuren, {'schiet_R': 'on',
                                                      'schiet_C': 'on',
                                                      'schiet_BB': 'on',
                                                      'schiet_TR': 'on',
                                                      'schiet_LB': 'on'})
        self.assert_is_redirect_not_plein(resp)

        # zet een wedstrijd voorkeur voor Recurve en informatie voorkeur voor Barebow
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R', sporter__lid_nr=lid_nr)
        sporterboog.voor_wedstrijd = True
        sporterboog.heeft_interesse = False
        sporterboog.save(update_fields=['voor_wedstrijd', 'heeft_interesse'])

        for boog in ('C', 'TR', 'LB'):
            sporterboog = SporterBoog.objects.get(boogtype__afkorting=boog, sporter__lid_nr=lid_nr)
            sporterboog.heeft_interesse = False
            sporterboog.save(update_fields=['heeft_interesse'])
        # for

    @staticmethod
    def _competitie_aanmaken():
        maak_competities_en_zet_fase_c()

    def test_inschrijven(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as sporter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/sporter-bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'eigen blazoen')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, sporterboog.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        inschrijving = RegiocompetitieSporterBoog.objects.first()
        self.assertEqual(str(inschrijving.ag_voor_indiv), "8.180")
        self.assertEqual(str(inschrijving.ag_voor_team), "8.180")
        self.assertFalse(inschrijving.ag_voor_team_mag_aangepast_worden)
        self.assertEqual(inschrijving.regiocompetitie, deelcomp)
        self.assertEqual(inschrijving.sporterboog, sporterboog)
        self.assertEqual(inschrijving.bij_vereniging, sporterboog.sporter.bij_vereniging)
        self.assertFalse(inschrijving.inschrijf_voorkeur_team)
        self.assertEqual(inschrijving.inschrijf_notitie, '')
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'GN')
        self.assertTrue(str(RegiocompetitieSporterBoog) != '')                  # coverage only
        self.assertEqual(inschrijving.indiv_klasse.competitie.afstand, '18')     # juiste competitie?
        self.assertEqual(inschrijving.indiv_klasse.boogtype.afkorting, 'R')      # klasse compatibel met boogtype?

        # geen bevestig formulier indien al ingeschreven
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Sporter is al aangemeld')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        # 18m TR voor extra coverage
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='TR')
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/sporter-bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'eigen blazoen')

        # uitzondering: AG score zonder hist
        res = score_indiv_ag_opslaan(sporterboog, 18, 7.18, None, 'Test 2')
        self.assertTrue(res)
        ags = Aanvangsgemiddelde.objects.filter(doel=AG_DOEL_INDIV,
                                                sporterboog=sporterboog,
                                                afstand_meter=deelcomp.competitie.afstand)
        AanvangsgemiddeldeHist.objects.filter(ag=ags[0]).delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/sporter-bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))

        # schakel over naar de 25m1pijl, barebow
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='25', regio=self.ver.regio)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/sporter-bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'eigen blazoen')

        # schrijf in voor de 25m BB, zonder AG
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, sporterboog.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)

        inschrijving_25 = RegiocompetitieSporterBoog.objects.exclude(pk=inschrijving.pk)[0]
        self.assertEqual(inschrijving_25.indiv_klasse.competitie.afstand, '25')     # juiste competitie?
        self.assertEqual(inschrijving_25.indiv_klasse.boogtype.afkorting, 'BB')     # klasse compatibel met boogtype?

        # probeer dubbel in te schrijven
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, sporterboog.pk))
        self.assert404(resp, 'Sporter is al aangemeld')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)

        # competitie in verkeerde fase
        comp = deelcomp.competitie    # Competitie.objects.get(pk=deelcomp.competitie.pk)
        zet_competitie_fases(comp, 'K', 'K')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk))
        self.assert404(resp, 'Verkeerde competitie fase')

    def test_bad(self):
        # inschrijven als anon
        resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assert_is_redirect_login(resp)
        # self.assert404(resp, 'Sporter niet gevonden')

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # corner-case: afmelden als niet-lid
        self.testdata.account_admin.sporter_set.all().delete()
        resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assert403(resp, "Geen toegang")        # huidige rol is niet sporter
        # self.assert404(resp, 'Sporter niet gevonden')

        # haal de bevestig pagina op als BB
        url = self.url_bevestig_aanmelden % (0, 0)
        resp = self.client.get(url)
        self.assert403(resp)

        # inschrijven als inactief lid
        self.client.logout()
        self.e2e_login(self.account_geen_lid)
        resp = self.client.post(self.url_aanmelden % (0, 0))
        self.assert404(resp, 'Sporter niet gevonden')

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)

        # illegaal deelcomp nummer
        resp = self.client.post(self.url_aanmelden % (99999, sporterboog.pk))
        self.assert404(resp, 'Sporter of competitie niet gevonden')
        resp = self.client.get(self.url_bevestig_aanmelden % (999999, sporterboog.pk))
        self.assert404(resp, 'Sporter of competitie niet gevonden')

        # illegaal sporterboog nummer
        resp = self.client.post(self.url_aanmelden % (99999, 'hallo'))
        self.assert404(resp, 'Sporter of competitie niet gevonden')
        resp = self.client.get(self.url_bevestig_aanmelden % (999999, 'hallo'))
        self.assert404(resp, 'Sporter of competitie niet gevonden')

        # sporterboog hoort niet bij gebruiker
        self.client.logout()
        self.e2e_login(self.account_twee)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, sporterboog.pk))
        self.assert404(resp, 'Geen valide combinatie')

        # mismatch diverse zaken
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=Regio.objects.get(regio_nr=116))
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk))
        self.assert404(resp, 'Geen valide combinatie')

        # schietmomenten
        url = self.url_zeven_wedstrijden % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Inschrijving niet gevonden')

    def test_afmelden(self):
        # afmelden als anon
        resp = self.client.post(self.url_afmelden % 0)
        self.assert404(resp, 'Sporter niet gevonden')

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # corner-case: afmelden als niet-lid
        self.testdata.account_admin.sporter_set.all().delete()
        resp = self.client.post(self.url_afmelden % 0)
        self.assert404(resp, 'Sporter niet gevonden')

        # afmelden als inactief lid
        self.client.logout()
        self.e2e_login(self.account_geen_lid)
        resp = self.client.post(self.url_afmelden % 0)
        self.assert404(resp, 'Sporter niet gevonden')

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # aanmelden voor de 18m Recurve, met AG
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        sporterboog_18 = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog_18, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, sporterboog_18.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        inschrijving_18 = RegiocompetitieSporterBoog.objects.first()

        # aanmelden voor de 25m BB, zonder AG
        sporterboog_25 = SporterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='25', regio=self.ver.regio)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, sporterboog_25.pk))
        self.assert_is_redirect(resp, self.url_profiel)

        # afmelden van de 18m
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving_18.pk)
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        # illegaal inschrijving nummer
        resp = self.client.post(self.url_afmelden % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')

        # niet bestaand inschrijving nummer
        resp = self.client.post(self.url_afmelden % 'hoi')
        self.assert404(resp, 'Inschrijving niet gevonden')

        # sporterboog hoort niet bij gebruiker
        inschrijving_25 = RegiocompetitieSporterBoog.objects.first()
        self.client.logout()
        self.e2e_login(self.account_twee)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving_25.pk)
        self.assert403(resp)

    def test_afmelden_geen_voorkeur_meer(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # aanmelden voor de 18m Recurve, met AG
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        sporterboog_18 = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog_18, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, sporterboog_18.pk))
        self.assert_is_redirect(resp, self.url_profiel)
        inschrijving_18 = RegiocompetitieSporterBoog.objects.first()

        # voorkeur boogtype uitzetten
        sporterboog_18.voor_wedstrijd = False
        sporterboog_18.save()

        # afmelden van de 18m
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving_18.pk)
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)

    def test_inschrijven_team(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        # geef ook team schieten en opmerking door
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'yes', 'opmerking': 'Hallo daar!'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        inschrijving = RegiocompetitieSporterBoog.objects.first()
        self.assertEqual(str(inschrijving.ag_voor_indiv), "8.180")
        self.assertEqual(str(inschrijving.ag_voor_team), "8.180")
        self.assertFalse(inschrijving.ag_voor_team_mag_aangepast_worden)
        self.assertEqual(inschrijving.regiocompetitie, deelcomp)
        self.assertEqual(inschrijving.sporterboog, sporterboog)
        self.assertEqual(inschrijving.bij_vereniging, sporterboog.sporter.bij_vereniging)
        self.assertTrue(inschrijving.inschrijf_voorkeur_team)
        self.assertEqual(inschrijving.inschrijf_notitie, 'Hallo daar!')
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'GN')

        # schrijf in voor de 25m BB, zonder AG, als aspirant
        self.sporter1.geboorte_datum = datetime.date(year=timezone.now().year - 12, month=1, day=1)
        self.sporter1.save()
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='25', regio=self.ver.regio)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmelden % (deelcomp.pk, sporterboog.pk),
                                    {'wil_in_team': 'ja', 'opmerking': 'ben ik oud genoeg?'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 2)

        inschrijving = RegiocompetitieSporterBoog.objects.filter(sporterboog=sporterboog).first()
        self.assertEqual(inschrijving.inschrijf_notitie, 'ben ik oud genoeg?')
        self.assertFalse(inschrijving.inschrijf_voorkeur_team)

    def test_inschrijven_methode3_twee_dagdelen(self):
        regio_105 = Regio.objects.get(pk=105)
        self.ver.regio = regio_105
        self.ver.save()

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=regio_105)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = 'ZAT,ZOm'
        deelcomp.save()

        # log in as sporter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/sporter-bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'eigen blazoen')
        self.assertContains(resp, 'Zaterdag')
        self.assertContains(resp, 'Zondagmiddag')
        self.assertNotContains(resp, 's Avonds')
        self.assertNotContains(resp, 'Weekend')

        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        # schrijf in met een niet toegestaan dagdeel
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        resp = self.client.post(url, {'dagdeel': 'AV'})
        self.assert404(resp, 'Verzoek is niet compleet')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)

        # schrijf in met dagdeel, team schieten en opmerking door
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'on',
                                          'dagdeel': 'ZAT',
                                          'opmerking': 'Hallo nogmaals!\n' * 50})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        inschrijving = RegiocompetitieSporterBoog.objects.first()
        self.assertTrue(inschrijving.inschrijf_voorkeur_team)
        self.assertTrue(len(inschrijving.inschrijf_notitie) > 480)
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'ZAT')

        # bad dagdeel
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='BB')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        resp = self.client.post(url, {'dagdeel': 'XX'})
        self.assert404(resp, 'Verzoek is niet compleet')
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

    def test_inschrijven_methode3_alle_dagdelen(self):
        regio_105 = Regio.objects.get(pk=105)
        self.ver.regio = regio_105
        self.ver.save()

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=regio_105)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = ''   # alles toegestaan
        deelcomp.save()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/sporter-bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'eigen blazoen')
        self.assertContains(resp, 'Zaterdag')
        self.assertContains(resp, 'Zondag')
        self.assertContains(resp, 's Avonds')
        self.assertContains(resp, 'Weekend')

        # geef dagdeel door
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'dagdeel': 'AV'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        inschrijving = RegiocompetitieSporterBoog.objects.first()
        self.assertFalse(inschrijving.inschrijf_voorkeur_team)
        self.assertEqual(inschrijving.inschrijf_notitie, '')
        self.assertEqual(inschrijving.inschrijf_voorkeur_dagdeel, 'AV')

        self.assertEqual(str(inschrijving.ag_voor_indiv), "8.180")
        self.assertEqual(str(inschrijving.ag_voor_team), "8.180")
        self.assertFalse(inschrijving.ag_voor_team_mag_aangepast_worden)

    def test_inschrijven_aspirant(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter met een leeftijd waarbij het mis kan gaan
        # huidige: 2020
        # geboren: 2007
        # bereikt leeftijd: 2020-2007 = 13
        # wedstrijdleeftijd 2020: 13 --> Onder14
        # wedstrijdleeftijd 2021: 14 --> Onder18
        # als het programma het goed doet, komt de sporter dus in de Onder18 klasse
        self.sporter1.geboorte_datum = datetime.date(year=timezone.now().year - 13, month=1, day=2)
        self.sporter1.save()
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/sporter-bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'Onder 12')
        self.assertNotContains(resp, 'Onder 14')
        self.assertContains(resp, 'Onder 18')

        # probeer in te schrijven en controleer daarna de wedstrijdklasse waarin de sporter geplaatst is
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        inschrijving = RegiocompetitieSporterBoog.objects.first()
        self.assertEqual(inschrijving.regiocompetitie, deelcomp)
        self.assertEqual(inschrijving.sporterboog, sporterboog)

        klasse = inschrijving.indiv_klasse
        self.assertFalse('Onder 12' in klasse.beschrijving)
        self.assertFalse('Onder 14' in klasse.beschrijving)
        self.assertTrue('Onder 18' in klasse.beschrijving)
        self.assertEqual(klasse.boogtype, sporterboog.boogtype)

    def test_inschrijven_methode1(self):
        regio_101 = Regio.objects.get(pk=101)
        self.ver.regio = regio_101
        self.ver.save()

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=regio_101)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        deelcomp.save()

        # maak een aantal wedstrijden aan, als RCL van Regio 101
        functie_rcl101 = Functie.objects.get(rol='RCL', comp_type='18', regio=regio_101)
        self.e2e_wissel_naar_functie(functie_rcl101)

        # doe een POST om de eerste ronde aan te maken
        url = self.url_planning_regio % deelcomp.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

        ronde_pk = RegiocompetitieRonde.objects.filter(regiocompetitie=deelcomp).first().pk

        # haal de ronde planning op
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk
        with self.assert_max_queries(20):
            resp = self.client.get(url_ronde)
        self.assertEqual(resp.status_code, 200)     # 200 = OK

        # maak een wedstrijd aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url_ronde)
        self.assert_is_redirect_not_plein(resp)

        match_pk = CompetitieMatch.objects.first().pk

        # wijzig de instellingen van deze wedstrijd
        url_wed = self.url_wijzig_wedstrijd % match_pk
        with self.assert_max_queries(20):
            resp = self.client.post(url_wed, {'ver_pk': self.ver.pk,
                                              'wanneer': '2020-12-11', 'aanvang': '12:34'})
        self.assert_is_redirect(resp, url_ronde)

        # maak nog een paar wedstrijden aan (voor later gebruik)
        for lp in range(7):
            with self.assert_max_queries(20):
                resp = self.client.post(url_ronde)
            self.assert_is_redirect_not_plein(resp)
        # for

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/sporter-bevestig-aanmelden.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'eigen blazoen')
        self.assertContains(resp, 'Kies wanneer je wilt schieten')
        self.assertContains(resp, '11 december 2020 om 12:34')

        # special: zet het vastgestelde AG op 0.000
        score_indiv_ag_opslaan(sporterboog, 18, 0.0, None, 'Test')

        # doe de inschrijving
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'wedstrijd_%s' % match_pk: 'on',
                                          'wedstrijd_99999': 'on'})     # is ignored
        self.assert_is_redirect(resp, self.url_profiel)

        aanmelding = RegiocompetitieSporterBoog.objects.get(sporterboog=sporterboog)
        self.assertEqual(aanmelding.ag_voor_indiv, 0.0)
        self.assertEqual(aanmelding.ag_voor_team, 0.0)
        self.assertTrue(aanmelding.ag_voor_team_mag_aangepast_worden)

        # doe nog een inschrijving
        self.e2e_login(self.account_twee)
        self._prep_voorkeuren(100002)

        sporterboog2 = SporterBoog.objects.get(sporter__lid_nr=100002, boogtype__afkorting='R')

        # doe de inschrijving
        url = self.url_aanmelden % (deelcomp.pk, sporterboog2.pk)
        with self.assert_max_queries(22):
            resp = self.client.post(url, {'wedstrijd_%s' % match_pk: 'on'})
        self.assert_is_redirect(resp, self.url_profiel)

        aanmelding2 = RegiocompetitieSporterBoog.objects.get(sporterboog=sporterboog2)

        # terug naar de eerste sporter
        self.e2e_login(self.account_normaal)

        # probeer de schietmomenten van een andere schutter aan te passen
        url = self.url_zeven_wedstrijden % aanmelding2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

        # pas de schietmomenten aan
        url = self.url_zeven_wedstrijden % aanmelding.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/keuze-zeven-wedstrijden-methode1.dtl', 'plein/site_layout.dtl'))

        # wedstrijd behouden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % match_pk: 'on'})
        self.assert_is_redirect(resp, self.url_profiel)

        # wedstrijd verwijderen
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_profiel)

        # wedstrijd toevoegen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % match_pk: 'on'})
        self.assert_is_redirect(resp, self.url_profiel)

        # te veel wedstrijden toevoegen
        args = dict()
        for obj in CompetitieMatch.objects.all():
            args['wedstrijd_%s' % obj.pk] = 'on'
        # for
        with self.assert_max_queries(20):
            resp = self.client.post(url, args)
        self.assert_is_redirect(resp, self.url_profiel)

        # bad deelnemer_pk
        resp = self.client.post(self.url_zeven_wedstrijden % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')

        # special: probeer inschrijving met competitie in verkeerde fase
        zet_competitie_fases(deelcomp.competitie, 'K', 'K')
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wedstrijd_%s' % match_pk: 'on'})
        self.assert404(resp, 'Verkeerde competitie fase')

    def test_geen_klasse(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as schutter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # voorkeuren en AG zetten
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        # extreem: aanmelden zonder passende klasse
        # zet het min_ag te hoog
        for klasse in CompetitieIndivKlasse.objects.filter(competitie=deelcomp.competitie,
                                                           boogtype__afkorting='R',
                                                           min_ag__lt=8.0):
            klasse.min_ag = 8.2     # > 8.18 van zet_ag
            klasse.save(update_fields=['min_ag'])
        # for
        # verwijder alle klassen 'onbekend'
        for klasse in CompetitieIndivKlasse.objects.filter(is_onbekend=True):
            klasse.is_onbekend = False
            klasse.save(update_fields=['is_onbekend'])
        # for

        # haal de bevestig pagina op met het formulier
        url = self.url_bevestig_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Geen passende wedstrijdklasse')

        # probeer de post
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert404(resp, 'Geen passende wedstrijdklasse')

    def test_met_ag_teams(self):
        # sporter aanmelden zonder AG indiv maar met handmatig AG teams

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # log in as sporter
        self.client.logout()
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(100001)

        # schrijf in voor de 18m Recurve, met AG
        # geef ook team schieten en opmerking door
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 0)
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        res = score_teams_ag_opslaan(sporterboog, 18, 8.25, self.account_twee, 'Test')
        self.assertTrue(res)
        sleep(0.050)        # zorg iets van spreiding in de 'when'
        res = score_teams_ag_opslaan(sporterboog, 18, 8.18, self.account_twee, 'Test')
        self.assertTrue(res)

        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'yes', 'opmerking': 'Hallo daar!'})
        self.assert_is_redirect(resp, self.url_profiel)
        self.assertEqual(RegiocompetitieSporterBoog.objects.count(), 1)

        inschrijving = RegiocompetitieSporterBoog.objects.first()
        self.assertEqual(str(inschrijving.ag_voor_indiv), "0.000")
        self.assertEqual(str(inschrijving.ag_voor_team), "8.180")
        self.assertTrue(inschrijving.ag_voor_team_mag_aangepast_worden)
        self.assertEqual(inschrijving.regiocompetitie, deelcomp)
        self.assertEqual(inschrijving.sporterboog, sporterboog)
        self.assertEqual(inschrijving.bij_vereniging, sporterboog.sporter.bij_vereniging)
        self.assertTrue(inschrijving.inschrijf_voorkeur_team)


# end of file
