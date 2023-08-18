# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Registreer.definities import REGISTRATIE_FASE_DONE
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestVerenigingHWL(E2EHelpers, TestCase):

    """ tests voor de Vereniging applicatie, module gast-accounts """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_overzicht = '/vereniging/'
    url_ledenlijst = '/vereniging/leden-lijst/'
    url_voorkeuren = '/vereniging/leden-voorkeuren/'
    url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/'      # comp_pk
    url_ingeschreven = '/bondscompetities/deelnemen/leden-ingeschreven/%s/'  # deelcomp_pk
    url_sporter_voorkeuren = '/sporter/voorkeuren/%s/'                       # sporter_pk
    url_gast_accounts = '/vereniging/gast-accounts/'
    url_gast_details = '/vereniging/gast-accounts/%s/details/'               # lid_nr

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        regio_111 = NhbRegio.objects.get(regio_nr=111)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = regio_111
        ver.save()
        self.ver1 = ver

        # maak het lid aan dat SEC wordt
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Secretaris"
        sporter.email = "rdesecretaris@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

        self.account_sec = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

        # maak een vereniging aan voor de gasten
        self.ver_extern = NhbVereniging.objects.get(ver_nr=settings.EXTERN_VER_NR)

        self.functie_sec_extern = maak_functie("SEC extern", "SEC")
        self.functie_sec_extern.vereniging = self.ver_extern
        self.functie_sec_extern.save()
        self.functie_sec_extern.accounts.add(self.account_sec)

        # maak een gast-account aan
        gast = GastRegistratie(
                    lid_nr=800001,
                    fase=REGISTRATIE_FASE_DONE,
                    email="een@gasten.not",
                    email_is_bevestigd=True,
                    voornaam="Een",
                    achternaam="van de Gasten",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    geslacht="V",
                    eigen_sportbond_naam="Eigen bond",
                    eigen_lid_nummer="EB-1234",
                    club="Eigen club",
                    club_plaats="Eigen plaats",
                    land="Eigen land",
                    telefoon="+998877665544",
                    wa_id="",
                    logboek="")
        gast.save()
        self.gast_800001 = gast

        self.account_800001 = self.e2e_create_account(gast.lid_nr, gast.email, gast.voornaam)

        sporter = Sporter(
                    lid_nr=gast.lid_nr,
                    is_gast=True,
                    geslacht=gast.geslacht,
                    voornaam=gast.voornaam,
                    achternaam=gast.achternaam,
                    email=gast.email,
                    geboorte_datum=gast.geboorte_datum,
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.ver_extern,
                    account=self.account_800001)
        sporter.save()
        self.sporter_800001 = sporter

        gast.sporter = sporter
        gast.account = self.account_800001
        gast.save(update_fields=['sporter', 'account'])

    # def _create_histcomp(self):
    #     # (strategisch gekozen) historische data om klassengrenzen uit te bepalen
    #     hist_seizoen = HistCompSeizoen(seizoen='2018/2019', comp_type=HISTCOMP_TYPE_18,
    #                                    indiv_bogen=",".join(HIST_BOGEN_DEFAULT))
    #     hist_seizoen.save()
    #
    #     # record voor het volwassen lid
    #     rec = HistCompRegioIndiv(
    #                 seizoen=hist_seizoen,
    #                 rank=1,
    #                 sporter_lid_nr=self.sporter_100001.lid_nr,
    #                 sporter_naam=self.sporter_100001.volledige_naam(),
    #                 vereniging_nr=self.ver1.ver_nr,
    #                 vereniging_naam=self.ver1.naam,
    #                 boogtype='R',
    #                 score1=10,
    #                 score2=20,
    #                 score3=30,
    #                 score4=40,
    #                 score5=50,
    #                 score6=60,
    #                 score7=70,
    #                 totaal=80,
    #                 gemiddelde=5.321)
    #     rec.save()
    #
    #     # record voor het jeugdlid
    #     # record voor het volwassen lid
    #     rec = HistCompRegioIndiv(
    #                 seizoen=hist_seizoen,
    #                 rank=1,
    #                 sporter_lid_nr=self.sporter_100002.lid_nr,
    #                 sporter_naam=self.sporter_100002.volledige_naam(),
    #                 vereniging_nr=self.ver1.ver_nr,
    #                 vereniging_naam=self.ver1.naam,
    #                 boogtype='BB',
    #                 score1=10,
    #                 score2=20,
    #                 score3=30,
    #                 score4=40,
    #                 score5=50,
    #                 score6=60,
    #                 score7=70,
    #                 totaal=80,
    #                 gemiddelde=5.321)
    #     rec.save()

    # def _create_competitie(self):
    #     # BB worden
    #     self.e2e_login_and_pass_otp(self.testdata.account_bb)
    #     self.e2e_wisselnaarrol_bb()
    #     self.e2e_check_rol('BB')
    #
    #     self.assertEqual(CompetitieIndivKlasse.objects.count(), 0)
    #     competities_aanmaken()
    #     self.comp_18 = Competitie.objects.get(afstand='18')
    #     self.comp_25 = Competitie.objects.get(afstand='25')

    def test_sec_gast_accounts(self):
        # wordt SEC van de vereniging voor gast-accounts
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec_extern)
        self.e2e_check_rol('SEC')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/overzicht.dtl', 'plein/site_layout.dtl'))

        # haal de gast-accounts ledenlijst op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_accounts)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/gast-accounts.dtl', 'plein/site_layout.dtl'))

        # zet een last_login
        self.account_800001.last_login = timezone.now()
        self.account_800001.save(update_fields=['last_login'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_accounts)

        # ontkoppel het account
        self.sporter_800001.account = None
        self.sporter_800001.save(update_fields=['account'])
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/gast-accounts.dtl', 'plein/site_layout.dtl'))

        self.gast_800001.account = None
        self.gast_800001.save(update_fields=['account'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_accounts)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/gast-accounts.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_gast_accounts)

    def test_sec_gast_details(self):
        # wordt SEC van de vereniging voor gast-accounts
        self.e2e_login_and_pass_otp(self.account_sec)
        self.e2e_wissel_naar_functie(self.functie_sec_extern)
        self.e2e_check_rol('SEC')

        # haal de details van een gast-account op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % self.gast_800001.lid_nr)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/gast-account-details.dtl', 'plein/site_layout.dtl'))

        # niet bestaand nummer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_gast_details % 999999)
        self.assert404(resp, 'Slechte parameter')

        self.e2e_assert_other_http_commands_not_supported(self.url_gast_details % self.gast_800001.lid_nr)

# end of file
