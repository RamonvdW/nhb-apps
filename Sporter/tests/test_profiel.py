# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_date
from BasisTypen.definities import ORGANISATIE_KHSN
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestel.models import Bestelling
from Competitie.definities import DEELNAME_JA, DEELNAME_NEE, DEELNAME_ONBEKEND, INSCHRIJF_METHODE_1
from Competitie.models import (Regiocompetitie, RegiocompetitieSporterBoog, Kampioenschap, KampioenschapSporterBoog,
                               CompetitieIndivKlasse)
from Competitie.test_utils.tijdlijn import (zet_competitie_fase_regio_prep, zet_competitie_fase_regio_inschrijven,
                                            zet_competitie_fase_regio_wedstrijden,
                                            zet_competitie_fase_rk_prep, zet_competitie_fase_rk_wedstrijden,
                                            zet_competitie_fase_bk_prep, zet_competitie_fase_bk_wedstrijden)
from Competitie.tests.test_helpers import competities_aanmaken, maak_competities_en_zet_fase_c
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Rayon
from HistComp.definities import HISTCOMP_TYPE_18
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Locatie.definities import BAAN_TYPE_EXTERN
from Locatie.models import Locatie
from Records.models import IndivRecord
from Registreer.models import GastRegistratie
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterVoorkeuren, SporterBoog
from Sporter.operations import get_sporterboog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.testdata import TestData
from Vereniging.models import Vereniging, Secretaris
from Wedstrijden.definities import (INSCHRIJVING_STATUS_DEFINITIEF, WEDSTRIJD_STATUS_GEACCEPTEERD,
                                    WEDSTRIJD_DISCIPLINE_INDOOR)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
import datetime


class TestSporterProfiel(E2EHelpers, TestCase):

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
                    regio=self.regio)
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

        sec = Secretaris(vereniging=ver)
        sec.save()
        sec.sporters.add(sporter)
        self.sec = sec

        # geef dit account een record
        rec = IndivRecord(
                    discipline='18',
                    volg_nr=1,
                    soort_record="60p",
                    geslacht=sporter.geslacht,
                    leeftijdscategorie='J',
                    materiaalklasse="R",
                    sporter=sporter,
                    naam="Ramon de Tester",
                    datum=parse_date('2011-11-11'),
                    plaats="Top stad",
                    score=293,
                    max_score=300)
        rec.save()

        rec = IndivRecord(
                    discipline='18',
                    volg_nr=2,
                    soort_record="60p",
                    geslacht=sporter.geslacht,
                    leeftijdscategorie='J',
                    materiaalklasse="C",
                    sporter=sporter,
                    naam="Ramon de Tester",
                    datum=parse_date('2012-12-12'),
                    plaats="Top stad",
                    land='Verwegistan',     # noqa
                    score=290,
                    max_score=300)
        rec.save()

        rec = IndivRecord(
                    discipline='18',
                    volg_nr=3,
                    soort_record="60p",
                    geslacht=sporter.geslacht,
                    leeftijdscategorie='C',
                    materiaalklasse="C",
                    sporter=sporter,
                    naam="Ramon de Tester",
                    datum=parse_date('1991-12-12'),
                    plaats="",     # typisch voor oudere records
                    score=290,
                    max_score=300)
        rec.save()

        # geef dit account een goede en een slechte HistComp record
        hist_seizoen = HistCompSeizoen(
                            seizoen="2009/2010",
                            comp_type=HISTCOMP_TYPE_18,
                            indiv_bogen='R')
        hist_seizoen.save()

        indiv = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=100001,
                    sporter_naam="Ramon de Tester",
                    boogtype="R",
                    vereniging_nr=1000,
                    vereniging_naam="don't care",
                    score1=123,
                    score2=234,
                    score3=345,
                    score4=456,
                    score5=0,
                    score6=666,
                    score7=7,
                    laagste_score_nr=7,
                    totaal=1234,
                    gemiddelde=9.123)
        indiv.save()

        indiv.pk = None
        indiv.boogtype = "??"   # bestaat niet, on purpose
        indiv.save()

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

    def test_anon(self):
        # zonder login --> terug naar het plein
        resp = self.client.get(self.url_profiel)
        self.assert_is_redirect_login(resp, self.url_profiel)

        resp = self.client.get(self.url_profiel_test)
        self.assert_is_redirect_login(resp, self.url_profiel)

    def test_geen_ver(self):
        # log in as sporter
        self.e2e_login(self.account_normaal)

        self.sporter1.bij_vereniging = None
        self.sporter1.save(update_fields=['bij_vereniging'])

        resp = self.client.get(self.url_profiel_test)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))

    def test_geen_sec(self):
        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)

        # als er geen SEC gekoppeld is, dan wordt de secretaris van de vereniging gebruikt
        self.functie_sec.accounts.remove(self.account_normaal)

        with self.assert_max_queries(24):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # maak dit een vereniging zonder secretaris
        Secretaris.objects.filter(vereniging=self.ver).delete()

        with self.assert_max_queries(22):
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
        with self.assert_max_queries(22):
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

    def test_geen_wedstrijden(self):
        # doe een test met een persoonlijk lid - mag geen wedstrijden doen

        self.ver.geen_wedstrijden = True
        self.ver.save()

        # log in as sporter
        # account_normaal is lid bij vereniging
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

    def test_fase_a(self):
        # competitie aanmaken
        competities_aanmaken(jaar=2019)

        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)

        # competitie in fase A wordt niet getoond op profiel
        with self.assert_max_queries(22):
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

        with self.assert_max_queries(22):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Bestellingen')                           # titel kaartje
        self.assertContains(resp, 'Alle details van je bestellingen.')      # tekst op kaartje
        self.assertContains(resp, '/bestel/overzicht/')                     # href van het kaartje

    def test_wedstrijden(self):
        # log in as sporter
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)

        now = timezone.now()
        volgende_week = (now + datetime.timedelta(days=7)).date()
        sporterboog = SporterBoog.objects.select_related('boogtype').filter(sporter=self.sporter1).first()
        boogtype = sporterboog.boogtype
        klasse = KalenderWedstrijdklasse.objects.filter(boogtype=sporterboog.boogtype).first()

        locatie = Locatie(
                        naam='Test locatie',
                        baan_type=BAAN_TYPE_EXTERN,
                        discipline_indoor=True,
                        banen_18m=15,
                        max_sporters_18m=15*4,
                        adres='Sportstraat 1, Pijlstad',        # noqa
                        plaats='Pijlstad')
        locatie.save()
        locatie.verenigingen.add(self.ver)

        sessie = WedstrijdSessie(
                        datum=volgende_week,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        beschrijving='test',
                        max_sporters=20)
        sessie.save()
        sessie.wedstrijdklassen.add(klasse)

        wedstrijd = Wedstrijd(
                        titel='Test wedstrijd',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=volgende_week,
                        datum_einde=volgende_week,
                        inschrijven_tot=1,
                        organiserende_vereniging=self.ver,
                        locatie=locatie,
                        organisatie=ORGANISATIE_KHSN,
                        discipline=WEDSTRIJD_DISCIPLINE_INDOOR,
                        aantal_banen=locatie.banen_18m)
        wedstrijd.save()
        wedstrijd.boogtypen.add(boogtype)
        wedstrijd.wedstrijdklassen.add(klasse)
        wedstrijd.sessies.add(sessie)

        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            status=INSCHRIJVING_STATUS_DEFINITIEF,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=sporterboog,
                            wedstrijdklasse=klasse,
                            koper=self.account_normaal,
                            log='test')
        inschrijving.save()

        with self.assert_max_queries(22):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wedstrijden')
        self.assertContains(resp, 'Pijlstad')
        urls = self.extract_all_urls(resp)
        # print('urls: %s' % repr(urls))
        urls = [url for url in urls if url.startswith('/wedstrijden/inschrijven/kwalificatie-scores-doorgeven/')]
        self.assertEqual(0, len(urls))

        # herhaal met kwalificatie scores
        wedstrijd.eis_kwalificatie_scores = True
        wedstrijd.save(update_fields=['eis_kwalificatie_scores'])

        with self.assert_max_queries(22):
            resp = self.client.get(self.url_profiel)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Wedstrijden')
        self.assertContains(resp, 'Pijlstad')
        urls = self.extract_all_urls(resp)
        # print('urls: %s' % repr(urls))
        urls = [url for url in urls if url.startswith('/wedstrijden/inschrijven/kwalificatie-scores-doorgeven/')]
        self.assertEqual(1, len(urls))

    def test_gast(self):
        self.e2e_login(self.account_normaal)
        self.account_normaal.is_gast = True
        self.account_normaal.save(update_fields=['is_gast'])

        GastRegistratie(
                email='',
                account=self.account_normaal,
                sporter=None,
                voornaam='',
                achternaam='').save()

        resp = self.client.get(self.url_profiel)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.get(self.url_profiel_test % "gast", data={"tekst": "gast"})
        self.assert404(resp, 'Geen toegang')

    def test_competitie_case_1(self):
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

    def test_competitie_case_2(self):
        case_nr = 2
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

    def _stroom_door_naar_rk(self, deelnemer: RegiocompetitieSporterBoog) -> KampioenschapSporterBoog:

        kampioenschap = Kampioenschap.objects.get(competitie=deelnemer.regiocompetitie.competitie,
                                                  rayon=self.rayon)

        kampioen = KampioenschapSporterBoog(
                        kampioenschap=kampioenschap,
                        sporterboog=deelnemer.sporterboog,
                        indiv_klasse=deelnemer.indiv_klasse,
                        #deelname=DEELNAME_ONBEKEND
                        bij_vereniging=self.ver)
        kampioen.save()

        return kampioen

    def test_competitie_case_3(self):
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

    def test_competitie_case_4(self):
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

    def test_competitie_case_5(self):
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

    def test_competitie_case_6(self):
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

    def test_competitie_case_7a(self):
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

    def test_competitie_case_7b(self):
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

    def test_competitie_case_8(self):
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

    def test_competitie_case_9a(self):
        case_nr = "9a"
        case_tekst = 'RK prep, 1x doorgestroomd naar RK, deelname nog niet doorgegeven'
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18)
        self.assertEqual(kamp_rk18.deelname, DEELNAME_ONBEKEND)
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

    def test_competitie_case_9b(self):
        case_nr = "9b"
        case_tekst = 'RK prep, 1x doorgestroomd naar RK, deelname = NEE, kan nog wijzigen'
        self.e2e_login(self.account_normaal)
        self._prep_voorkeuren(self.sporter1)  # zet R als wedstrijdboog
        self._competitie_aanmaken()  # zet fase C, dus openbaar en klaar voor inschrijving
        deelnemer18, _ = self._regio_inschrijven(do_25=False)
        kamp_rk18 = self._stroom_door_naar_rk(deelnemer18)
        kamp_rk18.deelname = DEELNAME_NEE
        kamp_rk18.save(update_fields=['deelname'])
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

    def test_competitie_case_9c(self):
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
        resp = self.client.get(self.url_profiel_test % case_nr, data={"tekst": case_tekst})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.e2e_open_in_browser(resp, self.show_in_browser)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('sporter/profiel.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'Je hebt je gekwalificeerd voor het RK in Rayon 3')
        self.assertContains(resp, 'Op de RK lijst sta je op plaats 15')
        urls = self.extract_all_urls(resp, skip_menu=True)
        # print('urls:', urls)
        urls2 = [url for url in urls if '/bondscompetities/rk/wijzig-status-rk-deelname/' in url]
        self.assertEqual(len(urls2), 1)

    def test_competitie_case_10(self):
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


# end of file
