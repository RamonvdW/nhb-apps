# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils.dateparse import parse_date
from django.utils import timezone
from django.test import TestCase
from BasisTypen.models import BoogType
from Bestel.models import Bestelling
from Competitie.definities import DEELNAME_JA, DEELNAME_NEE, INSCHRIJF_METHODE_1
from Competitie.models import (Competitie, Regiocompetitie, RegiocompetitieSporterBoog,
                               Kampioenschap, KampioenschapSporterBoog)
from Competitie.tijdlijn import (zet_competitie_fases,
                                 zet_competitie_fase_regio_prep, zet_competitie_fase_regio_inschrijven,
                                 zet_competitie_fase_regio_wedstrijden, zet_competitie_fase_regio_afsluiten,
                                 zet_competitie_fase_rk_prep,
                                 zet_competitie_fase_afsluiten)
from Competitie.tests.test_helpers import competities_aanmaken, maak_competities_en_zet_fase_c
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Records.models import IndivRecord
from Score.models import Score, ScoreHist
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterVoorkeuren, SporterBoog
from Vereniging.models import Secretaris
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData
import datetime


class TestSporterProfiel(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Profiel """

    test_after = ('NhbStructuur', 'HistComp', 'Competitie', 'Functie')

    url_profiel = '/sporter/'
    url_voorkeuren = '/sporter/voorkeuren/'
    url_aanmelden = '/bondscompetities/deelnemen/aanmelden/%s/%s/'                 # deelcomp_pk, sporterboog_pk
    url_bevestig_inschrijven = '/bondscompetities/deelnemen/aanmelden/bevestig/'   # deelcomp_pk, sporterboog_pk
    url_afmelden = '/bondscompetities/deelnemen/afmelden/%s/'                      # deelnemer_pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        ver.save()
        self.ver = ver

        # maak een test lid aan
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.account = self.account_normaal
        sporter.email = sporter.account.email
        sporter.save()
        self.sporter1 = sporter

        functie_hwl = maak_functie('HWL ver 1000', 'HWL')
        functie_hwl.accounts.add(self.account_normaal)
        functie_hwl.nhb_ver = ver
        functie_hwl.bevestigde_email = 'hwl@groteclub.nl'
        functie_hwl.save()
        self.functie_hwl = functie_hwl

        functie_sec = maak_functie('SEC ver 1000', 'SEC')
        functie_sec.accounts.add(self.account_normaal)
        functie_sec.bevestigde_email = 'sec@groteclub.nl'
        functie_sec.nhb_ver = ver
        functie_sec.save()
        self.functie_sec = functie_sec

        sec = Secretaris(vereniging=ver)
        sec.save()
        sec.sporters.add(sporter)
        self.sec = sec

        # geef dit account een record
        rec = IndivRecord()
        rec.discipline = '18'
        rec.volg_nr = 1
        rec.soort_record = "60p"
        rec.geslacht = sporter.geslacht
        rec.leeftijdscategorie = 'J'
        rec.materiaalklasse = "R"
        rec.sporter = sporter
        rec.naam = "Ramon de Tester"
        rec.datum = parse_date('2011-11-11')
        rec.plaats = "Top stad"
        rec.score = 293
        rec.max_score = 300
        rec.save()

        rec = IndivRecord()
        rec.discipline = '18'
        rec.volg_nr = 2
        rec.soort_record = "60p"
        rec.geslacht = sporter.geslacht
        rec.leeftijdscategorie = 'J'
        rec.materiaalklasse = "C"
        rec.sporter = sporter
        rec.naam = "Ramon de Tester"
        rec.datum = parse_date('2012-12-12')
        rec.plaats = "Top stad"
        rec.land = 'Verwegistan'
        rec.score = 290
        rec.max_score = 300
        rec.save()

        rec = IndivRecord()
        rec.discipline = '18'
        rec.volg_nr = 3
        rec.soort_record = "60p"
        rec.geslacht = sporter.geslacht
        rec.leeftijdscategorie = 'C'
        rec.materiaalklasse = "C"
        rec.sporter = sporter
        rec.naam = "Ramon de Tester"
        rec.datum = parse_date('1991-12-12')
        rec.plaats = ""     # typisch voor oudere records
        rec.score = 290
        rec.max_score = 300
        rec.save()

        # geef dit account een goede en een slechte HistComp record
        histcomp = HistCompetitie()
        histcomp.seizoen = "2009/2010"
        histcomp.comp_type = "18"
        histcomp.boog_str = "don't care"
        histcomp.save()

        indiv = HistCompetitieIndividueel()
        indiv.histcompetitie = histcomp
        indiv.rank = 1
        indiv.sporter_lid_nr = 100001
        indiv.sporter_naam = "Ramon de Tester"
        indiv.boogtype = "R"
        indiv.vereniging_nr = 1000
        indiv.vereniging_naam = "don't care"
        indiv.score1 = 123
        indiv.score2 = 234
        indiv.score3 = 345
        indiv.score4 = 456
        indiv.score5 = 0
        indiv.score6 = 666
        indiv.score7 = 7
        indiv.laagste_score_nr = 7
        indiv.totaal = 1234
        indiv.gemiddelde = 9.123
        indiv.save()

        indiv.pk = None
        indiv.boogtype = "??"   # bestaat niet, on purpose
        indiv.save()

        self.boog_R = BoogType.objects.get(afkorting='R')

    def _prep_voorkeuren(self):
        # haal de voorkeuren op - hiermee worden de SporterBoog records aangemaakt
        with self.assert_max_queries(20):
            self.client.get(self.url_voorkeuren)

        # zet een wedstrijd voorkeur voor Recurve en informatie voorkeur voor Barebow
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        sporterboog.voor_wedstrijd = True
        sporterboog.heeft_interesse = False
        sporterboog.save()

        for boog in ('C', 'TR', 'LB'):
            sporterboog = SporterBoog.objects.get(boogtype__afkorting=boog)
            sporterboog.heeft_interesse = False
            sporterboog.save()
        # for

    def _competitie_aanmaken(self):
        # competitie aanmaken
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_c()

        # zet de inschrijving open
        now = timezone.now()
        for comp in Competitie.objects.all():
            comp.begin_fase_C = now.date()
            comp.save()
        # for

    def test_anon(self):
        # zonder login --> terug naar het plein
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_profiel)
        self.assert403(resp)

    def test_compleet(self):
        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_profiel)
        self.assertNotContains(resp, 'De volgende competities worden georganiseerd')

        # competitie aanmaken
        comp_18, comp_25 = maak_competities_en_zet_fase_c()

        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # controleer dat inschrijven mogelijk is
        with self.assert_max_queries(23):
            resp = self.client.get(self.url_profiel)
        self.assertContains(resp, 'De volgende competities worden georganiseerd')
        self.assertContains(resp, 'De inschrijving is open tot ')
        self.assertContains(resp, 'De volgende competities passen bij de bogen waar jij mee schiet')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls), 2)

        # schrijf de sporter in voor de 18m Recurve
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', nhb_regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(21):
            resp = self.client.post(url, {'opmerking': 'test van de 18m'})
        self.assert_is_redirect(resp, self.url_profiel)

        deelcomp = Regiocompetitie.objects.get(competitie__afstand='25', nhb_regio=self.ver.regio)

        # zet de 25m door naar fase F
        zet_competitie_fase_regio_wedstrijden(comp_25)     # zet einde_fase_F

        # controleer dat inschrijven nog mogelijk is voor 25m en uitschrijven voor 18m
        with self.assert_max_queries(23):
            resp = self.client.get(self.url_profiel)
        self.assertContains(resp, 'De volgende competities worden georganiseerd')
        self.assertContains(resp, 'De inschrijving is open tot ')     # 18m
        self.assertContains(resp, 'Aanmelden kan nog tot ')      # 25m
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls2), 1)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 1)

        # afmelden moet nog kunnen als de wedstrijdboog weer uitgezet is
        sporterboog_bb = SporterBoog.objects.get(boogtype__afkorting='R')
        sporterboog_bb.voor_wedstrijd = False
        sporterboog_bb.save()
        with self.assert_max_queries(25):
            resp = self.client.get(self.url_profiel)
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls2), 0)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 1)
        sporterboog_bb.voor_wedstrijd = True
        sporterboog_bb.save()

        # zet een IFAA boog aan
        sporterboog_ifaa = SporterBoog.objects.get(boogtype__afkorting='FSR')
        sporterboog_ifaa.voor_wedstrijd = True
        sporterboog_ifaa.save()

        # zet de barebow boog 'aan' en schrijf in voor 25m BB
        sporterboog_bb = SporterBoog.objects.get(boogtype__afkorting='BB')
        sporterboog_bb.voor_wedstrijd = True
        sporterboog_bb.save()
        url = self.url_aanmelden % (deelcomp.pk, sporterboog_bb.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'wil_in_team': 'on'})
        self.assert_is_redirect(resp, self.url_profiel)
        sporterboog_bb.voor_wedstrijd = False
        sporterboog_bb.save()

        # zet de 18m ook door naar fase G
        zet_competitie_fase_regio_afsluiten(comp_18)

        # haal de profiel pagina op
        with self.assert_max_queries(29):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'De inschrijving is gesloten')            # 18m
        self.assertContains(resp, 'Aanmelden kan nog tot ')    # 25m

        # zet aanvangsgemiddelden voor 18m en 25m
        Score.objects.all().delete()        # nieuw vastgestelde AG is van vandaag
        obj = SporterBoog.objects.get(boogtype__afkorting='R')
        score_indiv_ag_opslaan(obj, 18, 9.018, None, 'Test opmerking A')
        score_indiv_ag_opslaan(obj, 25, 2.5, None, 'Test opmerking B')

        with self.assert_max_queries(29):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertContains(resp, "2,500")
        self.assertContains(resp, "9,018")
        self.assertContains(resp, "Test opmerking A")
        self.assertContains(resp, "Test opmerking B")

        # variant met Score zonder ScoreHist
        ScoreHist.objects.all().delete()
        with self.assert_max_queries(29):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_profiel)

        # zet de 18m door naar RK fase
        # zet de 25m door naar BK fase
        zet_competitie_fases(comp_18, 'K', 'K')
        zet_competitie_fases(comp_25, 'P', 'P')
        with self.assert_max_queries(27):
            resp = self.client.get(self.url_profiel)
        self.assertContains(resp, 'Rayonkampioenschappen')      # 18m
        self.assertContains(resp, 'Bondskampioenschappen')      # 25m

    def test_geen_sec(self):
        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # als er geen SEC gekoppeld is, dan wordt de secretaris van de vereniging gebruikt
        self.functie_sec.accounts.remove(self.account_normaal)

        with self.assert_max_queries(22):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # maak dit een vereniging zonder secretaris
        Secretaris.objects.filter(vereniging=self.ver).delete()

        with self.assert_max_queries(21):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # geen vereniging
        self.sporter1.bij_vereniging = None
        self.sporter1.save()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_geen_wedstrijdbogen(self):
        # geen regiocompetities op profiel indien geen wedstrijdbogen

        # log in as sporter
        self.e2e_login(self.account_normaal)
        # self._prep_voorkeuren()       --> niet aanroepen, dan geen sporterboog

        # haal de profiel pagina op
        with self.assert_max_queries(41):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

        # check record
        self.assertContains(resp, 'Top stad')

        # check scores
        self.assertContains(resp, '666')

        # check the competities (geen)
        self.assertNotContains(resp, 'Regiocompetities')

    def test_geen_voorkeur_competities(self):
        # toon geen regiocompetities als de sporter geen interesse heeft

        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()
        self.client.logout()

        # zonder login --> terug naar het plein
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_profiel)
        self.assert403(resp)

        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # competitie wordt niet getoond in vroege fases
        zet_competitie_fase_regio_prep(self.comp_18)
        with self.assert_max_queries(22):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # met standaard voorkeuren worden de regiocompetities getoond
        voorkeuren, _ = SporterVoorkeuren.objects.get_or_create(sporter=self.sporter1)
        self.assertTrue(voorkeuren.voorkeur_meedoen_competitie)
        with self.assert_max_queries(23):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'De volgende competities worden georganiseerd')

        # uitgezet worden de regiocompetities niet getoond
        voorkeuren.voorkeur_meedoen_competitie = False
        voorkeuren.save()
        with self.assert_max_queries(22):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'De volgende competities worden georganiseerd')

        # schrijf de sporter in voor de 18m Recurve
        zet_competitie_fase_regio_inschrijven(self.comp_18)
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', nhb_regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'opmerking': 'test van de 18m'})
        self.assert_is_redirect(resp, self.url_profiel)

        # voorkeur net uitgezet, maar nog wel ingeschreven
        with self.assert_max_queries(23):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

    def test_geen_wedstrijden(self):
        # doe een test met een persoonlijk lid - mag geen wedstrijden doen

        self.ver.geen_wedstrijden = True
        self.ver.save()

        # log in as sporter
        # account_normaal is lid bij nhbver
        self.e2e_login(self.account_normaal)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'De volgende competities worden georganiseerd')

    def test_inschrijfmethode1(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # zet de regiocompetitie op inschrijfmethode 1
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', nhb_regio=self.ver.regio)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        deelcomp.save()

        # log in as sporter en prep voor inschrijving
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        # schrijf de sporter in voor de 18m Recurve
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_profiel)

        with self.assert_max_queries(23):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

    def test_fase_a(self):
        # competitie aanmaken
        competities_aanmaken(jaar=2019)

        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # competitie in fase A wordt niet getoond op profiel
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

    def test_bestelling(self):
        # log in as sporter
        self.e2e_login(self.account_normaal)

        Bestelling(
            bestel_nr=1,
            account=self.account_normaal,
            log='testje').save()

        with self.assert_max_queries(41):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Bestellingen')                           # titel kaartje
        self.assertContains(resp, 'Alle details van je bestellingen.')      # tekst op kaartje
        self.assertContains(resp, '/bestel/overzicht/')                     # href van het kaartje

    def test_rk(self):
        # controleer het melden van de RK deelname status

        comp_18, comp_25 = maak_competities_en_zet_fase_c()

        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren()

        # schrijf de sporter in voor de 18m Recurve
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', nhb_regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(21):
            resp = self.client.post(url, {'opmerking': 'test van de 18m'})
        self.assert_is_redirect(resp, self.url_profiel)

        self.assertEqual(1, RegiocompetitieSporterBoog.objects.count())
        deelnemer = RegiocompetitieSporterBoog.objects.all()[0]

        # ingeschreven en geen knop meer voor aanmelden
        with self.assert_max_queries(27):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

        # laat de sporter doorstromen naar het RK
        deelkamp_25 = Kampioenschap.objects.get(competitie__afstand='25', nhb_rayon=self.ver.regio.rayon)
        kamp = KampioenschapSporterBoog(
                    kampioenschap=deelkamp_25,
                    sporterboog=sporterboog,
                    indiv_klasse=deelnemer.indiv_klasse,  # don't care maar moet gezet zijn
                    bij_vereniging=self.ver,
                    volgorde=51,
                    rank=24,
                    gemiddelde=9)
        kamp.save()

        deelkamp_18 = Kampioenschap.objects.get(competitie__afstand='18', nhb_rayon=self.ver.regio.rayon)
        kamp = KampioenschapSporterBoog(
                        kampioenschap=deelkamp_18,
                        sporterboog=sporterboog,
                        indiv_klasse=deelnemer.indiv_klasse,        # don't care maar moet gezet zijn
                        bij_vereniging=self.ver,
                        volgorde=50,
                        rank=42,
                        gemiddelde=9)
        kamp.save()

        # regiocompetitie fase
        zet_competitie_fase_regio_wedstrijden(comp_18)

        # controleer pre-afmelden
        with self.assert_max_queries(27):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je bent ingeschreven')
        self.assertNotContains(resp, 'Je bent alvast afgemeld voor de Rayonkampioenschappen')

        deelnemer.inschrijf_voorkeur_rk_bk = False
        deelnemer.save(update_fields=['inschrijf_voorkeur_rk_bk'])

        with self.assert_max_queries(27):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je bent ingeschreven')
        self.assertContains(resp, 'Je bent alvast afgemeld voor de Rayonkampioenschappen')

        # RK fase
        zet_competitie_fase_rk_prep(comp_18)

        # kampioenschap deelname: onbekend
        with self.assert_max_queries(27):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het RK in Rayon')
        self.assertContains(resp, 'Op de RK lijst sta je op plaats 42')
        self.assertContains(resp, 'Laat de wedstrijdleider van jouw vereniging weten of je mee kan doen')

        # kampioenschap deelname: bevestigd
        kamp.deelname = DEELNAME_JA
        kamp.save(update_fields=['deelname'])

        with self.assert_max_queries(27):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het RK in Rayon')
        self.assertContains(resp, 'Op de RK lijst sta je op plaats 42')

        # kampioenschap deelname: afgemeld
        kamp.deelname = DEELNAME_NEE
        kamp.rank = 0
        kamp.save(update_fields=['deelname', 'rank'])

        with self.assert_max_queries(27):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het RK in Rayon')
        self.assertContains(resp, 'Je bent afgemeld')

        # BK fase
        zet_competitie_fases(comp_18, 'O', 'O')
        with self.assert_max_queries(25):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

        # afsluitende fase
        zet_competitie_fase_afsluiten(comp_18)
        with self.assert_max_queries(25):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

# end of file
