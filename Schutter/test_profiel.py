# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils.dateparse import parse_date
from django.test import TestCase
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Records.models import IndivRecord
from Overig.e2ehelpers import E2EHelpers
import datetime


class TestSchutterProfiel(E2EHelpers, TestCase):
    """ unit tests voor de Schutter applicatie, module Profiel """

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.nhb_nr = "1000"
        ver.regio = NhbRegio.objects.get(pk=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()

        # maak een test lid aan
        lid = NhbLid()
        lid.nhb_nr = 100001
        lid.geslacht = "M"
        lid.voornaam = "Ramon"
        lid.achternaam = "de Tester"
        lid.email = "rdetester@gmail.not"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.bij_vereniging = ver
        lid.account = self.account_normaal
        lid.save()

        # geef dit account een record
        rec = IndivRecord()
        rec.discipline = '18'
        rec.volg_nr = 1
        rec.soort_record = "60p"
        rec.geslacht = lid.geslacht
        rec.leeftijdscategorie = 'J'
        rec.materiaalklasse = "R"
        rec.nhb_lid = lid
        rec.naam = "Ramon de Tester"
        rec.datum = parse_date('2011-11-11')
        rec.plaats = "Topstad"
        rec.score = 293
        rec.max_score = 300
        rec.save()

        # geef dit account een goede en een slechte HistComp record
        histcomp = HistCompetitie()
        histcomp.seizoen = "2009/2010"
        histcomp.comp_type = "18"
        histcomp.klasse = "don't care"
        histcomp.save()

        indiv = HistCompetitieIndividueel()
        indiv.histcompetitie = histcomp
        indiv.rank = 1
        indiv.schutter_nr = 100001
        indiv.schutter_naam = "Ramon de Tester"
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

    def test_view(self):
        # zonder login --> terug naar het plein
        resp = self.client.get('/schutter/')
        self.assert_is_redirect(resp, '/plein/')

        # met schutter-login wel toegankelijk
        self.e2e_login(self.account_normaal)

        resp = self.client.get('/schutter/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('schutter/profiel.dtl', 'plein/site_layout.dtl'))
        self.e2e_assert_other_http_commands_not_supported('/schutter/')

        # check record
        self.assertContains(resp, 'Topstad')

        # check scores
        self.assertContains(resp, '666')

# end of file
