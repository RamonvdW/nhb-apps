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
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Rayon
from HistComp.definities import HISTCOMP_TYPE_18
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Locatie.definities import BAAN_TYPE_EXTERN
from Locatie.models import Locatie
from Records.models import IndivRecord
from Registreer.models import GastRegistratie
from Sporter.models import Sporter, SporterBoog
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


# end of file
