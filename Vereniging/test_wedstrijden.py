# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.models import Competitie, CompetitieKlasse, LAAG_REGIO, DeelCompetitie
from Competitie.operations import maak_deelcompetitie_ronde
from Competitie.test_competitie import maak_competities_en_zet_fase_b
from Schutter.models import SchutterBoog
from Wedstrijden.models import CompetitieWedstrijd, CompetitieWedstrijdUitslag
from Score.models import Score
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestVerenigingWedstrijden(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor Wedstrijden """

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

        # maak de SEC functie
        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.nhb_ver = ver
        self.functie_sec.save()

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak het lid aan dat WL wordt
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

        self.account_wl = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_wl.accounts.add(self.account_wl)

        lid.account = self.account_wl
        lid.save()
        self.nhblid_100001 = lid

        boog_ib = BoogType.objects.get(afkorting='IB')

        schutterboog = SchutterBoog(nhblid=lid,
                                    boogtype=boog_ib,
                                    voor_wedstrijd=True)
        schutterboog.save()
        self.schutterboog_100001 = schutterboog

        # maak een jeugdlid aan
        lid = NhbLid()
        lid.nhb_nr = 100002
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Jeugdschutter"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=2010, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100002 = lid

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        lid = NhbLid()
        lid.nhb_nr = 100012
        lid.geslacht = "V"
        lid.voornaam = "Andrea"
        lid.achternaam = "de Jeugdschutter"
        lid.email = ""
        lid.geboorte_datum = datetime.date(year=2010, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=10, day=10)
        lid.bij_vereniging = ver
        lid.save()
        self.nhblid_100012 = lid

        # maak het lid aan dat HWL wordt
        lid = NhbLid()
        lid.nhb_nr = 100003
        lid.geslacht = "V"
        lid.voornaam = "Ramona"
        lid.achternaam = "de Testerin"
        lid.email = "ramonatesterin@nhb.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver

        self.account_hwl = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_hwl)

        lid.account = self.account_hwl
        lid.save()
        self.nhblid_100003 = lid

        # maak het lid aan dat SEC wordt
        lid = NhbLid()
        lid.nhb_nr = 100004
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Secretaris"
        lid.email = "rdesecretaris@gmail.not"
        lid.geboorte_datum = datetime.date(year=1971, month=5, day=28)
        lid.sinds_datum = datetime.date(year=2000, month=1, day=31)
        lid.bij_vereniging = ver
        lid.save()

        self.account_sec = self.e2e_create_account(lid.nhb_nr, lid.email, lid.voornaam, accepteer_vhpg=True)
        self.functie_sec.accounts.add(self.account_sec)

        lid.account = self.account_sec
        lid.save()
        self.nhblid_100004 = lid

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = NhbVereniging()
        ver2.naam = "Andere Club"
        ver2.ver_nr = "1222"
        ver2.regio = self.regio_111
        # secretaris kan nog niet ingevuld worden
        ver2.save()
        self.nhbver2 = ver2

        # BB worden
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competitie aan die nodig is voor deze tests
        self._create_competitie()
        self._maak_wedstrijden()

        self.url_overzicht = '/vereniging/'
        self.url_ledenlijst = '/vereniging/leden-lijst/'
        self.url_voorkeuren = '/vereniging/leden-voorkeuren/'
        self.url_inschrijven = '/vereniging/leden-aanmelden/competitie/%s/'      # <comp_pk>
        self.url_ingeschreven = '/vereniging/leden-ingeschreven/competitie/%s/'  # <deelcomp_pk>
        self.url_schutter_voorkeuren = '/sporter/voorkeuren/%s/'                 # <nhblid_pk>
        self.url_wedstrijden = '/vereniging/wedstrijden/'
        self.url_uitslag_invoeren = '/vereniging/uitslag-invoeren/'

    def _create_competitie(self):
        self.assertEqual(CompetitieKlasse.objects.count(), 0)
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_b()

        self.deelcomp_regio = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                         nhb_regio=self.regio_111,
                                                         competitie__afstand=18)

    def _maak_wedstrijden(self):
        # maak een ronde + plan
        ronde = maak_deelcompetitie_ronde(self.deelcomp_regio)

        de_tijd = datetime.time(hour=20)

        # maak binnen het plan drie wedstrijden voor deze vereniging
        for volgnr in range(3):
            wedstrijd = CompetitieWedstrijd(
                            vereniging=self.nhbver1,
                            datum_wanneer=datetime.date(year=2020, month=1, day=5+volgnr*3),
                            tijd_begin_aanmelden=de_tijd,
                            tijd_begin_wedstrijd=de_tijd,
                            tijd_einde_wedstrijd=de_tijd)

            if volgnr <= 1:
                uitslag = CompetitieWedstrijdUitslag(max_score=300, afstand_meter=12)
                uitslag.save()
                wedstrijd.uitslag = uitslag
                wedstrijd.beschrijving = "Dit is een testje %s" % volgnr

            if volgnr == 1:
                score = Score(schutterboog=self.schutterboog_100001,
                              waarde=123,
                              afstand_meter=12)
                score.save()
                uitslag.scores.add(score)

            wedstrijd.save()
            ronde.plan.wedstrijden.add(wedstrijd)
        # for

        # maak voor de vereniging een wedstrijd die niets met de competitie te doen heeft
        wedstrijd = CompetitieWedstrijd(
                        vereniging=self.nhbver1,
                        datum_wanneer=datetime.date(year=2020, month=2, day=1),
                        tijd_begin_aanmelden=de_tijd,
                        tijd_begin_wedstrijd=de_tijd,
                        tijd_einde_wedstrijd=de_tijd)
        wedstrijd.save()
        self.wedstrijd = wedstrijd

    def test_wedstrijden_hwl(self):
        # login als HWL
        self.e2e_login_and_pass_otp(self.account_hwl)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # haal de lijst van wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/wedstrijden.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)

        # haal de lijst van wedstrijden waarvan de uitslag ingevoerd mag worden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_uitslag_invoeren)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/wedstrijden.dtl', 'plein/site_layout.dtl'))

        urls2 = self.extract_all_urls(resp, skip_menu=True)
        for url in urls2:
            self.assertTrue("/waarschijnlijke-deelnemers/" in url or url.startswith('/bondscompetities/scores/uitslag-invoeren/'))
        # for

    def test_wedstrijden_wl(self):
        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        # haal de lijst van wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/wedstrijden.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)

    def test_wedstrijden_sec(self):
        # login als SEC
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec)
        self.e2e_check_rol('SEC')

        # haal de lijst van wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/wedstrijden.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)

    def test_bad(self):
        # geen toegang tot de pagina
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assert403(resp)

# end of file
