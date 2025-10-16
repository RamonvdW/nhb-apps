# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Geo.models import Regio
from HistComp.definities import HISTCOMP_TYPE_25, HIST_BOGEN_DEFAULT
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestHistCompInterland(E2EHelpers, TestCase):
    """ unittests voor de HistComp applicatie, module Interland """

    url_interland = '/bondscompetities/hist/interland/'
    url_interland_download = '/bondscompetities/hist/interland/als-bestand/%s/'  # boog_type

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        self.regio_101 = Regio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio_101)
        ver.save()

        hist_seizoen = HistCompSeizoen(seizoen='2018/2019',
                                       comp_type=HISTCOMP_TYPE_25,
                                       indiv_bogen=",".join(HIST_BOGEN_DEFAULT))
        hist_seizoen.save()
        self.klasse_pk = hist_seizoen.pk

        # maak een jeugdlid aan (komt in BB jeugd zonder klasse onbekend)
        sporter = Sporter(
                        lid_nr=100002,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="het Testertje",
                        email="rdetestertje@gmail.not",
                        geboorte_datum=datetime.date(year=2019-15, month=3, day=4),
                        sinds_datum=datetime.date(year=2015, month=11, day=12),
                        bij_vereniging=ver)
        sporter.save()
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save(update_fields=['account'])

        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=sporter.lid_nr,
                    sporter_naam="wordt niet gebruikt",
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam="wordt niet gebruikt",
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=70,
                    laagste_score_nr=1,
                    totaal=80,
                    gemiddelde=5.321)
        rec.save()
        self.indiv_rec_pk = rec.pk

        # maak nog een lid aan, met te weinig scores
        sporter = Sporter(
                    lid_nr=10000,
                    geslacht="V",
                    voornaam="Ramona",
                    achternaam="het Tester",
                    email="mevrdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1969, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save(update_fields=['account'])

        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=sporter.lid_nr,
                    sporter_naam="wordt niet gebruikt",
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam="wordt niet gebruikt",
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=0,
                    score6=0,
                    score7=0,
                    laagste_score_nr=1,
                    totaal=80,
                    gemiddelde=6.123)
        rec.save()

        # maak nog een inactief lid aan
        sporter = Sporter(
                    lid_nr=100004,
                    geslacht="V",
                    voornaam="Weg",
                    achternaam="Is Weg",
                    email="mevrwegisweg@gmail.not",
                    geboorte_datum=datetime.date(year=1969, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=None,
                    account=None)
        sporter.save()

        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=sporter.lid_nr,
                    sporter_naam="wordt niet gebruikt",
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam="wordt niet gebruikt",
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=0,
                    laagste_score_nr=1,
                    totaal=80,
                    gemiddelde=7.123)
        rec.save()

        # maak nog een record aan voor een lid dat weg is
        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=999999,
                    sporter_naam="wordt niet gebruikt",
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam="wordt niet gebruikt",
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=70,
                    laagste_score_nr=1,
                    totaal=80,
                    gemiddelde=6.123)
        rec.save()

        # maak een aspirant aan (mag niet meedoen)
        sporter = Sporter(
                    lid_nr=100005,
                    geslacht="M",
                    voornaam="Appie",
                    achternaam="Rant",
                    email="aspriant@gmail.not",
                    geboorte_datum=datetime.date(year=2019-12, month=3, day=4),
                    sinds_datum=datetime.date(year=2015, month=11, day=12),
                    bij_vereniging=ver)
        sporter.save()
        sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save(update_fields=['account'])

        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen,
                    rank=1,
                    sporter_lid_nr=sporter.lid_nr,
                    sporter_naam="wordt niet gebruikt",
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam="wordt niet gebruikt",
                    score1=10,
                    score2=20,
                    score3=30,
                    score4=40,
                    score5=50,
                    score6=60,
                    score7=70,
                    laagste_score_nr=1,
                    totaal=80,
                    gemiddelde=9.998)
        rec.save()

    def test_interland(self):
        # anon
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland)
        self.assert403(resp)

        # log in als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('histcomp/interland.dtl', 'design/site_layout.dtl'))

    def test_download(self):
        url = self.url_interland_download % 'R'

        # anon
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # log in als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert200_is_bestand_csv(resp)

        # download een lege lijst
        HistCompRegioIndiv.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert200_is_bestand_csv(resp)

    def test_bad(self):
        # log in als BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # verkeerd boog type
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland_download % 'XX')
        self.assert404(resp, 'Verkeerd boog type')

        # verwijder de hele histcomp
        HistCompSeizoen.objects.all().delete()

        # haal het lege overzicht op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_interland_download % 'R')
        self.assert404(resp, 'Geen data')


# end of file
