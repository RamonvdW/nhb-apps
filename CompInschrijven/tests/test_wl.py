# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Competitie.models import Competitie, CompetitieIndivKlasse, Regiocompetitie
from Competitie.operations import competities_aanmaken
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompInschrijvenWL(E2EHelpers, TestCase):

    """ tests voor de CompInschrijven applicatie, functies voor de WL """

    test_after = ('BasisTypen', 'ImportCRM', 'Functie', 'Sporter', 'Competitie')

    url_aanmelden = '/bondscompetities/deelnemen/leden-aanmelden/%s/'        # <comp_pk>
    url_ingeschreven = '/bondscompetities/deelnemen/leden-ingeschreven/%s/'  # <deelcomp_pk>
    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'  # <sporter_pk>
    url_overzicht = '/vereniging/'

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

        # maak de WL functie
        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.vereniging = ver
        self.functie_wl.save()

        # maak het lid aan dat WL wordt
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

        self.account_wl = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)
        self.functie_wl.accounts.add(self.account_wl)

        sporter.account = self.account_wl
        sporter.save()
        self.sporter_100001 = sporter

        # maak een jeugdlid aan
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="de Jeugdschutter",
                    email="",
                    geboorte_datum=datetime.date(year=2010, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100002 = sporter

        # maak nog een jeugdlid aan, in dezelfde leeftijdsklasse
        sporter = Sporter(
                    lid_nr=100012,
                    geslacht="V",
                    voornaam="Andrea",
                    achternaam="de Jeugdschutter",
                    email="",
                    geboorte_datum=datetime.date(year=2010, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=10, day=10),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100012 = sporter

        # maak een senior lid aan, om inactief te maken
        sporter = Sporter(
                    lid_nr=100003,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="de Testerin",
                    email="",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        self.sporter_100003 = sporter

        # maak een lid aan van een andere vereniging
        # maak een test vereniging
        ver2 = Vereniging(
                    naam="Andere Club",
                    ver_nr=1222,
                    regio=self.regio_111)
        ver2.save()
        self.ver2 = ver2

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
        competities_aanmaken()
        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        self.deelcomp_regio = Regiocompetitie.objects.get(regio=self.regio_111,
                                                          competitie__afstand=18)

    def test_inschrijven(self):
        url = self.url_aanmelden % self.comp_18.pk

        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)       # WL mag dit niet

    def test_ingeschreven(self):
        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        url = self.url_ingeschreven % self.deelcomp_regio.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('compinschrijven/hwl-leden-ingeschreven.dtl', 'plein/site_layout.dtl'))

        # probeer in te schrijven (mag niet)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_cornercase(self):
        # login als WL
        self.e2e_login_and_pass_otp(self.account_wl)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        resp = self.client.get(self.url_ingeschreven % 9999999)
        self.assert404(resp, 'Verkeerde parameters')

# end of file
