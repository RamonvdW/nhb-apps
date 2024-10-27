# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from BasisTypen.models import BoogType
from Competitie.definities import DEELNAME_JA, DEELNAME_NEE, DEELNAME_ONBEKEND, INSCHRIJF_METHODE_1, DEEL_BK
from Competitie.models import (Regiocompetitie, RegiocompetitieSporterBoog, Kampioenschap, KampioenschapSporterBoog,
                               CompetitieIndivKlasse, CompetitieMatch)
from Competitie.test_utils.tijdlijn import (zet_competitie_fase_regio_prep, zet_competitie_fase_regio_inschrijven,
                                            zet_competitie_fase_regio_wedstrijden,
                                            zet_competitie_fase_rk_prep, zet_competitie_fase_rk_wedstrijden,
                                            zet_competitie_fase_bk_prep, zet_competitie_fase_bk_wedstrijden)
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Rayon
from Locatie.models import WedstrijdLocatie
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterVoorkeuren, SporterBoog
from Sporter.operations import get_sporterboog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData
from Vereniging.models import Vereniging
import datetime


class TestSporterProfielBondscompetities(E2EHelpers, TestCase):

    """ tests voor de Sporter applicatie, module Profiel """

    test_after = ('ImportCRM', 'HistComp', 'Competitie', 'Functie')

    url_profiel = '/sporter/'
    url_voorkeuren = '/sporter/voorkeuren/'
    url_aanmelden = '/bondscompetities/deelnemen/aanmelden/%s/%s/'                 # deelcomp_pk, sporterboog_pk
    url_bevestig_inschrijven = '/bondscompetities/deelnemen/aanmelden/bevestig/'   # deelcomp_pk, sporterboog_pk
    url_afmelden = '/bondscompetities/deelnemen/afmelden/%s/'                      # deelnemer_pk
    url_profiel_test = '/sporter/profiel-test/%s/'                                 # test case nummer

    testdata = None
    show_in_browser = False

    @classmethod
    def setUpTestData(cls):
        cls.testdata = TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.show_in_browser = cls.is_small_test_run()

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        self.regio = Regio.objects.get(pk=111)
        self.rayon = Rayon.objects.get(rayon_nr=self.regio.rayon_nr)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio,
                    plaats='Boogstad')
        ver.save()
        self.ver = ver

        loc = WedstrijdLocatie(
                    naam='Grote Club',
                    discipline_25m1pijl=True,
                    discipline_indoor=True,
                    banen_18m=12,
                    banen_25m=12,
                    max_sporters_18m=4*12,
                    max_sporters_25m=4*12,
                    adres='Schietweg 5\n9999ZZ ' + ver.plaats,
                    plaats=ver.plaats,
                    notities='Gratis WiFi')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc = loc

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
        self.sporterboog = None

        functie_hwl = maak_functie('HWL ver 1000', 'HWL')
        functie_hwl.accounts.add(self.account_normaal)
        functie_hwl.vereniging = ver
        functie_hwl.bevestigde_email = 'hwl@groteclub.nl'
        functie_hwl.save()
        self.functie_hwl = functie_hwl

        functie_sec = maak_functie('SEC ver 1000', 'SEC')
        functie_sec.accounts.add(self.account_normaal)
        functie_sec.bevestigde_email = 'sec@groteclub.nl'
        functie_sec.vereniging = ver
        functie_sec.save()
        self.functie_sec = functie_sec

        self.boog_R = BoogType.objects.get(afkorting='R')

    def _prep_voorkeuren(self, sporter):
        get_sporterboog(sporter, mag_database_wijzigen=True)

        # zet een wedstrijd voorkeur voor Recurve en informatie voorkeur voor Barebow
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        sporterboog.voor_wedstrijd = True
        sporterboog.heeft_interesse = False
        sporterboog.save()
        self.sporterboog = sporterboog

        for boog in ('C', 'TR', 'LB'):
            sporterboog = SporterBoog.objects.get(boogtype__afkorting=boog)
            sporterboog.heeft_interesse = False
            sporterboog.save()
        # for

    def _competitie_aanmaken(self):
        # competitie aanmaken
        # en de inschrijving open zetten
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_c()

    def _maak_kampioenschap_match(self, kamp: KampioenschapSporterBoog):
        # maak een competitie match met adres wedstrijdlocatie

        rk_bk = kamp.kampioenschap

        match = CompetitieMatch(
                    competitie=rk_bk.competitie,
                    beschrijving='Test',
                    vereniging=self.ver,
                    locatie=self.loc,
                    datum_wanneer='2000-01-01',
                    tijd_begin_wedstrijd='09:00',
                    aantal_scheids=1)
        match.save()

        match.indiv_klassen.add(kamp.indiv_klasse)

        rk_bk.rk_bk_matches.add(match)

    def test_inschrijfmethode1(self):
        # log in as BB en maak de competitie aan
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self._competitie_aanmaken()

        # zet de regiocompetitie op inschrijfmethode 1
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        deelcomp.save()

        # print('Aantal Competitie: %s' % Competitie.objects.count())
        # comp_18 = deelcomp.competitie
        # comp_18.bepaal_fase()
        # from Functie.rol import Rollen
        # comp_18.bepaal_openbaar(Rollen.ROL_SPORTER)
        # print('comp_18: %s' % comp_18)
        # print('comp_18.fase_indiv=%s, fase_teams=%s' % (comp_18.fase_indiv, comp_18.fase_teams))
        # print('comp_18.is_openbaar=%s' % comp_18.is_openbaar)

        # log in as sporter en prep voor inschrijving
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)

        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)

        # schrijf de sporter in voor de 18m Recurve
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(21):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_profiel)

        with self.assert_max_queries(26):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

    def test_case_01(self):
        case_nr = "1a"
        case_tekst = 'geen bondscompetities'
        self.e2e_login(self.account_normaal)

        # geen competities
        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'De volgende competities worden georganiseerd')
        self.assertContains(resp, 'Er worden op dit moment geen competities georganiseerd')

        # competities in de "prep" fase
        case_nr = "1b"
        case_tekst = 'bondscompetities in prep fase'
        self._competitie_aanmaken()
        zet_competitie_fase_regio_prep(self.comp_18)
        zet_competitie_fase_regio_prep(self.comp_25)
        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'De volgende competities worden georganiseerd')
        self.assertContains(resp, 'Er worden op dit moment geen competities georganiseerd')

        # geen voorkeur voor competities
        case_nr = "1c"
        case_tekst = 'geen voorkeur voor bondscompetities'
        zet_competitie_fase_regio_inschrijven(self.comp_18)
        zet_competitie_fase_regio_inschrijven(self.comp_25)
        self._prep_voorkeuren(self.sporter1)
        voorkeuren, _ = SporterVoorkeuren.objects.get_or_create(sporter=self.sporter1)
        self.assertTrue(voorkeuren.voorkeur_meedoen_competitie)
        voorkeuren.voorkeur_meedoen_competitie = False
        voorkeuren.save(update_fields=['voorkeur_meedoen_competitie'])
        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, 'De volgende competities worden georganiseerd')

    def test_case_02a(self):
        case_nr = "2a"
        case_tekst = 'niet ingeschreven, kan inschrijven op beide competities met recurve boog'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'De volgende competities worden georganiseerd')
        self.assertContains(resp, 'De inschrijving is open tot ')
        self.assertContains(resp, 'De volgende competities passen bij de bogen waar jij mee schiet')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls), 2)

    def test_case_02b(self):
        case_nr = "2b"
        case_tekst = 'niet ingeschreven, geen boog ingesteld'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)
        self.sporterboog.voor_wedstrijd = False
        self.sporterboog.save(update_fields=['voor_wedstrijd'])
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'De volgende competities worden georganiseerd')
        self.assertContains(resp, 'De inschrijving is open tot ')
        self.assertContains(resp, 'Pas je persoonlijke voorkeuren aan')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls), 0)

    def _regio_inschrijven(self, do_18=True, do_25=True, wil_rk_18=True, wil_rk_25=True):
        if do_18:
            regiocomp18 = Regiocompetitie.objects.get(competitie=self.comp_18, regio=self.ver.regio)
            indiv18 = (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=self.comp_18,
                               boogtype=self.boog_R)
                       .order_by('volgorde')  # klasse 1 eerst
                       .first())

            deelnemer18 = RegiocompetitieSporterBoog(
                                regiocompetitie=regiocomp18,
                                sporterboog=self.sporterboog,
                                bij_vereniging=self.ver,
                                # ag_voor_indiv="10,000",
                                # ag_voor_team="10,000",
                                ag_voor_team_mag_aangepast_worden=False,
                                indiv_klasse=indiv18,
                                # inschrijf_voorkeur_team=False,
                                inschrijf_voorkeur_rk_bk=wil_rk_18,
                                # inschrijf_voorkeur_dagdeel=
                                # inschrijf_gekozen_matches=
                                aangemeld_door=self.account_normaal)

            deelnemer18.save()
        else:
            deelnemer18 = None

        if do_25:
            regiocomp25 = Regiocompetitie.objects.get(competitie=self.comp_25, regio=self.ver.regio)
            indiv25 = (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=self.comp_25,
                               boogtype=self.boog_R)
                       .order_by('volgorde')  # klasse 1 eerst
                       .first())

            deelnemer25 = RegiocompetitieSporterBoog(
                                regiocompetitie=regiocomp25,
                                sporterboog=self.sporterboog,
                                bij_vereniging=self.ver,
                                # ag_voor_indiv="10,000",
                                # ag_voor_team="10,000",
                                ag_voor_team_mag_aangepast_worden=False,
                                indiv_klasse=indiv25,
                                # inschrijf_voorkeur_team=False,
                                inschrijf_voorkeur_rk_bk=wil_rk_25,
                                # inschrijf_voorkeur_dagdeel=
                                # inschrijf_gekozen_matches=
                                aangemeld_door=self.account_normaal)

            deelnemer25.save()
        else:
            deelnemer25 = None

        return deelnemer18, deelnemer25

    def _stroom_door_naar_rk(self, deelnemer: RegiocompetitieSporterBoog, set_rank=False) -> KampioenschapSporterBoog:

        kampioenschap = Kampioenschap.objects.get(competitie=deelnemer.regiocompetitie.competitie,
                                                  rayon=self.rayon)

        kamp_rk = KampioenschapSporterBoog(
                        kampioenschap=kampioenschap,
                        sporterboog=deelnemer.sporterboog,
                        indiv_klasse=deelnemer.indiv_klasse,
                        # deelname=DEELNAME_ONBEKEND
                        bij_vereniging=self.ver)

        if set_rank:
            kamp_rk.rank = 5

        kamp_rk.save()

        return kamp_rk

    @staticmethod
    def _stroom_door_naar_bk(kamp_rk: KampioenschapSporterBoog) -> KampioenschapSporterBoog:

        kampioenschap_bk = Kampioenschap.objects.get(competitie=kamp_rk.kampioenschap.competitie,
                                                     deel=DEEL_BK)

        kamp_bk = KampioenschapSporterBoog(
                        kampioenschap=kampioenschap_bk,
                        sporterboog=kamp_rk.sporterboog,
                        indiv_klasse=kamp_rk.indiv_klasse,
                        bij_vereniging=kamp_rk.bij_vereniging)
        kamp_bk.save()

        return kamp_bk

    def test_case_03(self):
        case_nr = 3
        case_tekst = '1x ingeschreven + mogelijkheid tot uitschrijven'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        self._regio_inschrijven(do_18=False)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls2), 1)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 1)

    def test_case_04(self):
        case_nr = 4
        case_tekst = '2x ingeschreven, afgemeld voor RK 25m1pijl + mogelijkheid tot uitschrijven'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        self._regio_inschrijven(wil_rk_25=False)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je bent alvast afgemeld')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/regio/voorkeur-rk/' in url]
        self.assertEqual(len(urls2), 2)     # 1 per inschrijving. Knop kan "voorkeur" of "aanpassen" heten.

    def test_case_05(self):
        case_nr = 5
        case_tekst = '1x nog ingeschreven'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        self._regio_inschrijven(do_25=False)

        # zet de wedstrijdboog uit
        self.sporterboog.voor_wedstrijd = False
        self.sporterboog.save(update_fields=['voor_wedstrijd'])

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Deze boog is niet meer ingesteld als wedstrijdboog')
        self.assertContains(resp, 'Je bent nog ingeschreven')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 1)

    def test_case_06(self):
        # zet alle regio's over naar inschrijfmethode 1
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        Regiocompetitie.objects.update(inschrijf_methode=INSCHRIJF_METHODE_1)

        case_nr = "6a"
        case_tekst = 'wedstrijdmomenten aanpassen, tijdens inschrijven'
        self._regio_inschrijven(do_25=False)
        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/regio/keuze-zeven-wedstrijden/' in url]
        self.assertEqual(len(urls2), 1)

        # zet wedstrijden fase
        case_nr = "6b"
        case_tekst = 'wedstrijdmomenten aanpassen, tijdens wedstrijden fase'
        zet_competitie_fase_regio_wedstrijden(self.comp_18)
        zet_competitie_fase_regio_wedstrijden(self.comp_25)
        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/regio/keuze-zeven-wedstrijden/' in url]
        self.assertEqual(len(urls2), 1)

    def test_case_07a(self):
        case_nr = "7a"
        case_tekst = '1x ingeschreven, uitschrijven kan niet meer, 1x laat aanmelden mogelijk, voorkeur RK instellen'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        self._regio_inschrijven(do_25=False)
        zet_competitie_fase_regio_wedstrijden(self.comp_18)
        zet_competitie_fase_regio_wedstrijden(self.comp_25)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls2), 1)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 0)
        urls2 = [url for url in urls if '/bondscompetities/regio/voorkeur-rk/' in url]
        self.assertEqual(len(urls2), 1)

    def test_case_07b(self):
        case_nr = "7b"
        case_tekst = '2x ingeschreven, voorkeur RK: is afgemeld, kan aangepast worden'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        self._regio_inschrijven(wil_rk_25=False)
        zet_competitie_fase_regio_wedstrijden(self.comp_18)
        zet_competitie_fase_regio_wedstrijden(self.comp_25)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls2), 0)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 0)
        urls2 = [url for url in urls if '/bondscompetities/regio/voorkeur-rk/' in url]
        self.assertEqual(len(urls2), 2)

    def test_case_07c(self):
        case_nr = "7c"
        case_tekst = '1x ingeschreven, boog is uitgezet, uitschrijven kan niet meer'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        self._regio_inschrijven(do_25=False)

        # boog weer 'uit' zetten
        self.sporterboog.voor_wedstrijd = False
        self.sporterboog.save(update_fields=['voor_wedstrijd'])

        zet_competitie_fase_regio_wedstrijden(self.comp_18)
        zet_competitie_fase_regio_wedstrijden(self.comp_25)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/aanmelden/' in url]
        self.assertEqual(len(urls2), 0)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 0)
        urls2 = [url for url in urls if '/bondscompetities/regio/voorkeur-rk/' in url]
        self.assertEqual(len(urls2), 0)

    def test_case_08(self):
        case_nr = 8
        case_tekst = 'RK prep, niet gekwalificeerd voor RK'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        zet_competitie_fase_rk_prep(self.comp_25)
        zet_competitie_fase_rk_prep(self.comp_18)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je bent geen deelnemer in het RK')
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 0)
        urls2 = [url for url in urls if '/bondscompetities/rk/wijzig-status-rk-deelname/' in url]
        self.assertEqual(len(urls2), 0)

    def test_case_09a(self):
        case_nr = "9a"
        case_tekst = 'RK prep, 1x doorgestroomd naar RK, deelname nog niet doorgegeven'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18, set_rank=True)
        self.assertEqual(kamp_rk18.deelname, DEELNAME_ONBEKEND)
        self._maak_kampioenschap_match(kamp_rk18)
        zet_competitie_fase_rk_prep(self.comp_25)
        zet_competitie_fase_rk_prep(self.comp_18)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het RK in Rayon 3')
        self.assertContains(resp, 'Laat weten of je mee kan doen')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/rk/wijzig-status-rk-deelname/' in url]
        self.assertEqual(len(urls2), 2)

    def test_case_09b(self):
        case_nr = "9b"
        case_tekst = 'RK prep, 1x doorgestroomd naar RK, deelname = NEE, kan nog wijzigen'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18)
        kamp_rk18.deelname = DEELNAME_NEE
        kamp_rk18.save(update_fields=['deelname'])
        self._maak_kampioenschap_match(kamp_rk18)
        zet_competitie_fase_rk_prep(self.comp_25)
        zet_competitie_fase_rk_prep(self.comp_18)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het RK in Rayon 3')
        self.assertContains(resp, 'Je bent afgemeld')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/rk/wijzig-status-rk-deelname/' in url]
        self.assertEqual(len(urls2), 1)

    def test_case_09c(self):
        case_nr = "9c"
        case_tekst = 'RK prep, 1x doorgestroomd naar RK, deelname = JA, kan nog wijzigen'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        zet_competitie_fase_rk_prep(self.comp_18)
        zet_competitie_fase_rk_wedstrijden(self.comp_25)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18)
        kamp_rk18.deelname = DEELNAME_JA
        kamp_rk18.rank = 15
        kamp_rk18.save(update_fields=['deelname', 'rank'])
        self._maak_kampioenschap_match(kamp_rk18)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het RK in Rayon 3')
        self.assertContains(resp, 'Op de RK lijst sta je op plaats 15')
        self.assertContains(resp, 'Schietweg 5')
        self.assertContains(resp, '9999ZZ Boogstad')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/rk/wijzig-status-rk-deelname/' in url]
        self.assertEqual(len(urls2), 1)

    def test_case_09d(self):
        case_nr = "9d"
        case_tekst = 'RK prep, 1x doorgestroomd naar RK, deelname nog niet doorgegeven, nog geen locatie'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18, set_rank=True)
        self.assertEqual(kamp_rk18.deelname, DEELNAME_ONBEKEND)
        zet_competitie_fase_rk_prep(self.comp_25)
        zet_competitie_fase_rk_prep(self.comp_18)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Laat weten of je mee kan doen')
        self.assertContains(resp, 'volgt binnenkort')

    def test_case_09e(self):
        case_nr = "9e"
        case_tekst = 'RK prep, 1x doorgestroomd naar RK, deelname = JA, kan nog wijzigen, nog geen locatie'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        zet_competitie_fase_rk_prep(self.comp_18)
        zet_competitie_fase_rk_wedstrijden(self.comp_25)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18)
        kamp_rk18.deelname = DEELNAME_JA
        kamp_rk18.rank = 15
        kamp_rk18.save(update_fields=['deelname', 'rank'])

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'volgt binnenkort')

    def test_case_10(self):
        case_nr = 10
        case_tekst = 'BK prep, niet gekwalificeerd voor BK'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)        # zet R als wedstrijdboog
        self._competitie_aanmaken()                 # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        zet_competitie_fase_rk_prep(self.comp_25)
        zet_competitie_fase_bk_prep(self.comp_18)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je bent geen deelnemer in het BK')
        urls = self.extract_all_urls(resp, skip_menu=True)
        urls2 = [url for url in urls if '/bondscompetities/deelnemen/afmelden/' in url]
        self.assertEqual(len(urls2), 0)
        urls2 = [url for url in urls if '/bondscompetities/rk/wijzig-status-rk-deelname/' in url]
        self.assertEqual(len(urls2), 0)

    def test_case_11a(self):
        case_nr = "11a"
        case_tekst = 'BK prep, 1x doorgestroomd naar BK, deelname nog niet doorgegeven'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18)
        kamp_bk18 = self._stroom_door_naar_bk(kamp_rk18)
        zet_competitie_fase_bk_prep(self.comp_18)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het BK')
        self.assertContains(resp, 'Laat weten of je mee kan doen')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/bk/wijzig-status-bk-deelname/' in url]
        self.assertEqual(len(urls2), 2)     # TODO: waarom 2?

    def test_case_11b(self):
        case_nr = "11b"
        case_tekst = 'BK prep, 1x doorgestroomd naar BK, deelname = NEE, kan nog wijzigen'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18)
        kamp_bk18 = self._stroom_door_naar_bk(kamp_rk18)
        kamp_bk18.deelname = DEELNAME_NEE
        kamp_bk18.save(update_fields=['deelname'])
        zet_competitie_fase_bk_prep(self.comp_18)
        zet_competitie_fase_bk_prep(self.comp_25)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het BK')
        self.assertContains(resp, 'Je bent afgemeld')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/bk/wijzig-status-bk-deelname/' in url]
        self.assertEqual(len(urls2), 1)

    def test_case_11c(self):
        case_nr = "11c"
        case_tekst = 'BK prep, 1x doorgestroomd naar BK, deelname = JA, kan nog wijzigen'

        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        zet_competitie_fase_rk_prep(self.comp_18)
        zet_competitie_fase_rk_wedstrijden(self.comp_25)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18)
        kamp_bk18 = self._stroom_door_naar_bk(kamp_rk18)
        kamp_bk18.deelname = DEELNAME_JA
        kamp_bk18.rank = 12
        kamp_bk18.save(update_fields=['deelname', 'rank'])
        zet_competitie_fase_bk_prep(self.comp_18)
        zet_competitie_fase_bk_prep(self.comp_25)

        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het BK')
        self.assertContains(resp, 'Op de BK lijst sta je op plaats 12')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/bk/wijzig-status-bk-deelname/' in url]
        self.assertEqual(len(urls2), 1)

    def test_testserver(self):
        with override_settings(IS_TEST_SERVER=False):
            case_nr = 0
            case_tekst = 'test server'
            resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
            self.assertEqual(resp.status_code, 410)

# end of file
