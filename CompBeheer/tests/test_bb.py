# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.operations import maak_functie
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Competitie.models import (Competitie, DeelCompetitie, DeelKampioenschap,
                               CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMutatie,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2, INSCHRIJF_METHODE_3, DAGDEEL_AFKORTINGEN)
from Competitie.operations import competities_aanmaken, aanvangsgemiddelden_vaststellen_voor_afstand
from Competitie.tests.test_fase import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompBeheerTestBB(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module BB """

    test_after = ('BasisTypen', 'Functie', 'Competitie.tests.test_fase')

    url_kies = '/bondscompetities/'
    url_overzicht = '/bondscompetities/%s/'
    url_aanmaken = '/bondscompetities/beheer/aanmaken/'
    url_instellingen = '/bondscompetities/beheer/instellingen-volgende-competitie/'
    url_wijzigdatums = '/bondscompetities/beheer/%s/wijzig-datums/'                             # comp_pk
    url_ag_vaststellen_afstand = '/bondscompetities/beheer/ag-vaststellen/%s/'                  # afstand
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp_pk
    url_klassengrenzen_tonen = '/bondscompetities/%s/klassengrenzen-tonen/'                     # comp_pk
    url_seizoen_afsluiten = '/bondscompetities/beheer/seizoen-afsluiten/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # deze test is afhankelijk van de standaard regio's
        self.regio_101 = regio = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = 1000
        ver.regio = regio
        ver.save()

        # maak een volwassen test lid aan (komt in groep met klasse onbekend)
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = "rdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        self.account_lid = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_lid
        sporter.save()
        self.sporter_100001 = sporter

        self.functie_hwl = maak_functie('HWL test', 'HWL')
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_lid)

        # maak een jeugdlid aan (komt in BB jeugd zonder klasse onbekend)
        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "het Testertje"
        sporter.email = "rdetestertje@gmail.not"
        sporter.geboorte_datum = datetime.date(year=2008, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2015, month=11, day=12)
        sporter.bij_vereniging = ver
        self.account_jeugdlid = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_jeugdlid
        sporter.save()
        self.sporter_100002 = sporter

        boog_bb = BoogType.objects.get(afkorting='BB')
        boog_tr = BoogType.objects.get(afkorting='TR')

        # maak een sporterboog aan voor het jeugdlid (nodig om aan te melden)
        sporterboog = SporterBoog(sporter=self.sporter_100002, boogtype=boog_bb, voor_wedstrijd=False)
        sporterboog.save()
        self.sporterboog_100002 = sporterboog

        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "V"
        sporter.voornaam = "Zus"
        sporter.achternaam = "de Testerin"
        sporter.email = "zus@gmail.not"
        sporter.geboorte_datum = datetime.date(year=2008, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2015, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100003 = sporter

        # maak een sporterboog aan voor het lid (nodig om aan te melden)
        sporterboog = SporterBoog(sporter=self.sporter_100003, boogtype=boog_bb, voor_wedstrijd=True)
        sporterboog.save()
        self.sporterboog_100003 = sporterboog

        # maak een sporterboog aan voor het lid (nodig om aan te melden)
        sporterboog = SporterBoog(sporter=self.sporter_100001, boogtype=boog_tr, voor_wedstrijd=True)
        sporterboog.save()

        # (strategisch gekozen) historische data om klassengrenzen uit te bepalen
        histcomp = HistCompetitie()
        histcomp.seizoen = '2018/2019'
        histcomp.comp_type = '18'
        histcomp.boog_str = 'Testcurve1'       # TODO: kan de klasse een spatie bevatten?
        histcomp.is_team = False
        histcomp.save()
        self.histcomp = histcomp

        # een ouder seizoen dat niet gebruikt moet worden
        histcomp2 = HistCompetitie()
        histcomp2.seizoen = '2017/2018'
        histcomp2.comp_type = '18'
        histcomp2.boog_str = 'Testcurve2'
        histcomp2.is_team = False
        histcomp2.save()

        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.sporter_lid_nr = self.sporter_100001.lid_nr
        rec.sporter_naam = self.sporter_100001.volledige_naam()
        rec.vereniging_nr = ver.ver_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'R'
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()

        # nog een record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp2
        rec.rank = 1
        rec.sporter_lid_nr = self.sporter_100001.lid_nr
        rec.sporter_naam = self.sporter_100001.volledige_naam()
        rec.vereniging_nr = ver.ver_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'R'
        rec.score1 = 11
        rec.score2 = 21
        rec.score3 = 31
        rec.score4 = 41
        rec.score5 = 51
        rec.score6 = 61
        rec.score7 = 71
        rec.totaal = 81
        rec.gemiddelde = 6.12
        rec.save()

        # nog een record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 100
        rec.sporter_lid_nr = self.sporter_100001.lid_nr
        rec.sporter_naam = self.sporter_100001.volledige_naam()
        rec.vereniging_nr = ver.ver_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'TR'
        rec.score1 = 11
        rec.score2 = 21
        rec.score3 = 31
        rec.score4 = 41
        rec.score5 = 51
        rec.score6 = 61
        rec.score7 = 71
        rec.totaal = 81
        rec.gemiddelde = 6.12
        rec.save()

        # maak een record aan zonder eindgemiddelde
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.sporter_lid_nr = self.sporter_100002.lid_nr
        rec.sporter_naam = self.sporter_100002.volledige_naam()
        rec.vereniging_nr = ver.ver_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'C'
        rec.score1 = 0
        rec.score2 = 0
        rec.score3 = 0
        rec.score4 = 0
        rec.score5 = 0
        rec.score6 = 0
        rec.score7 = 0
        rec.totaal = 0
        rec.gemiddelde = 0.0
        rec.save()

        # record voor het jeugdlid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.sporter_lid_nr = self.sporter_100002.lid_nr
        rec.sporter_naam = self.sporter_100002.volledige_naam()
        rec.vereniging_nr = ver.ver_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'BB'
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()

        # maak een record aan voor iemand die geen lid meer is
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.sporter_lid_nr = 991111
        rec.sporter_naam = "Die is weg"
        rec.vereniging_nr = ver.ver_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'BB'
        rec.score1 = 10
        rec.score2 = 20
        rec.score3 = 30
        rec.score4 = 40
        rec.score5 = 50
        rec.score6 = 60
        rec.score7 = 70
        rec.totaal = 80
        rec.gemiddelde = 5.321
        rec.save()

    def _maak_many_histcomp(self):
        # maak veel histcomp records aan
        # zodat de AG-vaststellen bulk-create limiet van 500 gehaald wordt

        lid_nr = 190000
        records = list()
        sporters = list()

        geboorte_datum = datetime.date(year=1970, month=3, day=4)
        sinds_datum = datetime.date(year=2001, month=11, day=12)

        for lp in range(550):
            sporter = Sporter(
                            lid_nr=lid_nr + lp,
                            geslacht='V',
                            geboorte_datum=geboorte_datum,
                            sinds_datum=sinds_datum)
            sporters.append(sporter)

            rec = HistCompetitieIndividueel(histcompetitie=self.histcomp,
                                            boogtype='R',
                                            rank=lp,
                                            sporter_lid_nr=sporter.lid_nr,
                                            vereniging_nr=1000,
                                            score1=1,
                                            score2=2,
                                            score3=3,
                                            score4=4,
                                            score5=5,
                                            score6=6,
                                            score7=250,
                                            totaal=270,
                                            gemiddelde=5.5)
            records.append(rec)
        # for

        Sporter.objects.bulk_create(sporters)
        HistCompetitieIndividueel.objects.bulk_create(records)

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_instellingen)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmaken)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen_afstand % '18')
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_vaststellen % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_seizoen_afsluiten)
        self.assert403(resp)

    def test_instellingen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_instellingen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-instellingen-nieuwe-competitie.dtl', 'plein/site_layout.dtl'))

    def test_aanmaken(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-competities-aanmaken.dtl', 'plein/site_layout.dtl'))

        # gebruik een post om de competitie aan te laten maken
        # geen parameters nodig
        self.assertEqual(Competitie.objects.count(), 0)
        self.assertEqual(DeelCompetitie.objects.count(), 0)
        self.assertEqual(0, CompetitieMutatie.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken, {'snel': 1})
        self.assert_is_redirect(resp, self.url_kies)
        self.assertEqual(1, CompetitieMutatie.objects.count())       # voor achtergrondtaak

    def test_dubbel_aanmaken(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # probeer de competities aan te maken terwijl ze al bestaan
        # verifieer geen effect
        competities_aanmaken()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-competities-aanmaken.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wat doe je hier?")

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        self.assertEqual(Competitie.objects.count(), 2)
        self.assertEqual(DeelCompetitie.objects.count(), 2*16)
        self.assertEqual(DeelKampioenschap.objects.count(), 2*5)

    def test_regio_settings_overnemen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.assertEqual(DeelCompetitie.objects.count(), 0)

        # maak een competitie aan
        competities_aanmaken(jaar=2019)

        dagdelen_105_18 = "%s,%s,%s" % (DAGDEEL_AFKORTINGEN[0], DAGDEEL_AFKORTINGEN[1], DAGDEEL_AFKORTINGEN[2])
        dagdelen_105_25 = "%s,%s,%s" % (DAGDEEL_AFKORTINGEN[3], DAGDEEL_AFKORTINGEN[4], DAGDEEL_AFKORTINGEN[0])

        # pas regio-instellingen aan
        deelcomp = DeelCompetitie.objects.get(
                                competitie__afstand=18,
                                nhb_regio__regio_nr=101)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        deelcomp.save()

        deelcomp = DeelCompetitie.objects.get(
                                competitie__afstand=18,
                                nhb_regio__regio_nr=105)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = dagdelen_105_18
        deelcomp.save()

        deelcomp = DeelCompetitie.objects.get(
                                competitie__afstand=25,
                                nhb_regio__regio_nr=105)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = dagdelen_105_25
        deelcomp.save()

        # maak opnieuw een competitie aan
        # maak een competitie aan
        competities_aanmaken(jaar=2020)

        # controleer dat de settings overgenomen zijn
        for deelcomp in (DeelCompetitie
                         .objects
                         .select_related('competitie', 'nhb_regio')
                         .filter(nhb_regio__regio_nr=101)):
            if deelcomp.competitie.afstand == '18':
                self.assertEqual(deelcomp.inschrijf_methode, INSCHRIJF_METHODE_1)
            else:
                self.assertEqual(deelcomp.inschrijf_methode, INSCHRIJF_METHODE_2)
        # for

        for deelcomp in (DeelCompetitie
                         .objects
                         .select_related('competitie', 'nhb_regio')
                         .filter(nhb_regio__regio_nr=105)):
            self.assertEqual(deelcomp.inschrijf_methode, INSCHRIJF_METHODE_3)
            if deelcomp.competitie.afstand == '18':
                self.assertEqual(deelcomp.toegestane_dagdelen, dagdelen_105_18)
            else:
                self.assertEqual(deelcomp.toegestane_dagdelen, dagdelen_105_25)
        # for

    def test_ag_vaststellen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        # trigger de permissie check (want: verkeerde rol)
        self.e2e_wisselnaarrol_gebruiker()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen_afstand % '18')
        self.assert403(resp)

        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # trigger de onbekende afstand fout
        resp = self.client.get(self.url_ag_vaststellen_afstand % '42')
        self.assert404(resp, 'Onbekende afstand')

        resp = self.client.post(self.url_ag_vaststellen_afstand % '42')
        self.assert404(resp, 'Onbekende afstand')

        # trigger de permissie check (want: geen competitie aangemaakt)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen_afstand % '18')
        self.assert404(resp, 'Geen competitie in de juiste fase')

        # maak de competities aan - de voorwaarde om AG's vast te stellen
        competities_aanmaken()

        comp = Competitie.objects.get(afstand=25, is_afgesloten=False)

        # controleer dat het "ag vaststellen" kaartje er is
        # om te beginnen zonder "voor het laatst gedaan"
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_ag_vaststellen_afstand % comp.afstand in urls)
        self.assertNotContains(resp, "laatst gedaan op")

        # verander de fase van de 25m competitie zodat we verschillen hebben
        comp = Competitie.objects.get(afstand=25, is_afgesloten=False)
        CompetitieIndivKlasse(competitie=comp, volgorde=1, min_ag=25.0, boogtype=self.sporterboog_100002.boogtype).save()
        comp.klassengrenzen_vastgesteld = True
        comp.save()

        # maak nog een hele bak AG's aan
        self._maak_many_histcomp()

        # haal het AG scherm op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen_afstand % comp.afstand)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # probeer de AG's te laten vaststellen terwijl dat niet meer mag
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_ag_vaststellen_afstand % '25', {'snel': 1})
        self.assert404(resp, 'Geen competitie in de juiste fase')

        # aanmaken wordt gedaan door de achtergrondtaak, maar die draait nu niet
        aanvangsgemiddelden_vaststellen_voor_afstand(18)
        aanvangsgemiddelden_vaststellen_voor_afstand(25)

        # controleer dat er geen dubbele SporterBoog records aangemaakt zijn
        self.assertEqual(1, SporterBoog.objects.filter(sporter=self.sporter_100001, boogtype__afkorting='R').count())
        self.assertEqual(1, SporterBoog.objects.filter(sporter=self.sporter_100002, boogtype__afkorting='BB').count())
        self.assertEqual(14954, SporterBoog.objects.count())

        # controleer dat het "ag vaststellen" kaartje er nog steeds is
        # dit keer met de "voor het laatst gedaan" notitie
        comp = Competitie.objects.get(afstand=18, is_afgesloten=False)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(self.url_ag_vaststellen_afstand % 18 in urls)
        self.assertContains(resp, "laatst gedaan op")

    def test_ag_vaststellen_cornercases(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # maak de competities aan - de voorwaarde om AG's vast te stellen
        competities_aanmaken()

        # geen HistCompIndividueel
        HistCompetitieIndividueel.objects.all().delete()

        # haal het AG scherm op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen_afstand % 18)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # probeer de POST
        with self.assert_max_queries(15):
            resp = self.client.post(self.url_ag_vaststellen_afstand % 18,
                                    {'snel': 1})
        self.assert_is_redirect_not_plein(resp)

        # geen HistComp
        HistCompetitie.objects.all().delete()

        # haal het AG scherm op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen_afstand % 18)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)

        # probeer de POST
        with self.assert_max_queries(5):
            resp = self.client.post(self.url_ag_vaststellen_afstand % 18,
                                    {'snel': 1})
        self.assert_is_redirect_not_plein(resp)

    def test_klassengrenzen_vaststellen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competities aan - de voorwaarde om AG's vast te stellen
        competities_aanmaken()

        # 18m competitie
        comp18 = Competitie.objects.filter(afstand='18')[0]
        comp18_pk = comp18.pk
        url = self.url_klassengrenzen_vaststellen % comp18_pk

        with self.assert_max_queries(22, check_duration=False):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-klassengrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))

        # nu kunnen we met een POST de klassengrenzen vaststellen
        count = CompetitieIndivKlasse.objects.filter(competitie=comp18, min_ag__gt=0).count()
        self.assertEqual(count, 0)
        with self.assert_max_queries(97):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)        # redirect = success
        count = CompetitieIndivKlasse.objects.filter(competitie=comp18, min_ag__gt=0).count()
        self.assertTrue(count > 20)
        # TODO: check nog meer velden van de aangemaakte objecten

        # coverage: nog een keer vaststellen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)             # 200 = OK

        count1 = CompetitieIndivKlasse.objects.filter(competitie=comp18).count()
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)        # redirect = success
        count2 = CompetitieIndivKlasse.objects.filter(competitie=comp18).count()
        self.assertEqual(count1, count2)

        # coverage
        obj = CompetitieIndivKlasse.objects.filter(is_voor_rk_bk=False)[0]
        self.assertTrue(str(obj) != "")
        obj = CompetitieIndivKlasse.objects.filter(is_voor_rk_bk=True)[0]
        self.assertTrue(str(obj) != "")
        obj = CompetitieTeamKlasse.objects.filter(is_voor_teams_rk_bk=False)[0]
        self.assertTrue(str(obj) != "")
        obj = CompetitieTeamKlasse.objects.filter(is_voor_teams_rk_bk=True)[0]
        self.assertTrue(str(obj) != "")

    def test_klassengrenzen_vaststellen_cornercases(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        competities_aanmaken()

        # illegale competitie
        resp = self.client.get(self.url_klassengrenzen_vaststellen % 'xx')
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_klassengrenzen_vaststellen % 'xx')
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_klassengrenzen_tonen % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

    def test_klassengrenzen_tonen(self):
        # competitie opstarten
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competities aan
        competities_aanmaken()
        comp_18 = Competitie.objects.filter(afstand=18).all()[0]
        comp_25 = Competitie.objects.filter(afstand=25).all()[0]

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_tonen % comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassengrenzen-tonen.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, 'De klassengrenzen zijn nog niet vastgesteld')

        # klassengrenzen vaststellen (18m en 25m)
        # s1 = timezone.now()
        with self.assert_max_queries(97):
            resp = self.client.post(self.url_klassengrenzen_vaststellen % comp_18.pk)
        # s2 = timezone.now()
        # print('duration:', s2-s1)
        self.assert_is_redirect_not_plein(resp)        # redirect = success
        with self.assert_max_queries(97):
            resp = self.client.post(self.url_klassengrenzen_vaststellen % comp_25.pk)
        self.assert_is_redirect_not_plein(resp)        # redirect = success

        # kies pagina ophalen als BB, dan worden alle competities getoond
        zet_competitie_fase(comp_18, 'B')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

        self.e2e_logout()

        # kies pagina ophalen als bezoeker
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

        # nog een keer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_tonen % comp_25.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassengrenzen-tonen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, ' zijn nog niet vastgesteld')
        self.assertNotContains(resp, 'De klassengrenzen voor de ')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_tonen % comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassengrenzen-tonen.dtl', 'plein/site_layout.dtl'))
        self.assertNotContains(resp, ' zijn nog niet vastgesteld')
        self.assertNotContains(resp, 'De klassengrenzen voor de ')

    def test_wijzig_datums(self):
        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=2019)
        # nu in fase A

        comp = Competitie.objects.all()[0]

        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.begin_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.einde_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.einde_teamvorming)
        self.assertEqual(datetime.date(year=2019, month=12, day=31), comp.eerste_wedstrijd)

        # niet BB
        url = self.url_wijzigdatums % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        # wordt BB
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # get
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-wijzig-datums.dtl', 'plein/site_layout.dtl'))

        # post
        with self.assert_max_queries(21):
            resp = self.client.post(url, {'datum1': '2019-08-09',
                                          'datum2': '2019-09-10',
                                          'datum3': '2019-10-11',
                                          'datum4': '2019-11-12',
                                          'datum5': '2019-11-12',
                                          'datum6': '2020-02-01',
                                          'datum7': '2019-02-12',
                                          'datum8': '2020-05-01',
                                          'datum9': '2020-05-12',
                                          'datum10': '2020-06-12',
                                          })
        self.assert_is_redirect(resp, self.url_overzicht % comp.pk)

        # controleer dat de nieuwe datums opgeslagen zijn
        comp = Competitie.objects.get(pk=comp.pk)
        self.assertEqual(datetime.date(year=2019, month=8, day=9), comp.begin_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=9, day=10), comp.einde_aanmeldingen)
        self.assertEqual(datetime.date(year=2019, month=10, day=11), comp.einde_teamvorming)
        self.assertEqual(datetime.date(year=2019, month=11, day=12), comp.eerste_wedstrijd)

        # check corner cases

        # alle datums verplicht
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': '2019-08-09'})
        self.assert404(resp, 'Verplichte parameter ontbreekt')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum1': 'null',
                                          'datum2': 'hallo',
                                          'datum3': '0',
                                          'datum4': '2019-13-42'})
        self.assert404(resp, 'Geen valide datum')

        # foute comp_pk bij get
        url = self.url_wijzigdatums % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # foute comp_pk bij post
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')

    def test_seizoen_afsluiten(self):
        # moet BB zijn
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # maak een competitie van het volgende seizoen aan
        competities_aanmaken(jaar=2019)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen_afsluiten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-seizoen-afsluiten.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_seizoen_afsluiten)
        self.assert404(resp, 'Alle competities nog niet in fase S')

        # maak een HistComp aan die straks doorgezet gaat worden
        hist = HistCompetitie(
                        seizoen='2019/2020',
                        is_openbaar=False,
                        boog_str='Test',
                        comp_type='18')
        hist.save()

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # fase S: alle BK's afgesloten
        zet_competitie_fase(self.comp_18, 'S')
        zet_competitie_fase(self.comp_25, 'S')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen_afsluiten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-seizoen-afsluiten.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_seizoen_afsluiten)
        self.assert_is_redirect(resp, '/bondscompetities/')

        hist = HistCompetitie.objects.get(pk=hist.pk)
        self.assertTrue(hist.is_openbaar)

        # corner case: verwijder alle competitie
        Competitie.objects.all().delete()

        resp = self.client.get(self.url_seizoen_afsluiten)
        self.assert404(resp, 'Geen competitie gevonden')

        resp = self.client.post(self.url_seizoen_afsluiten)
        self.assert404(resp, 'Geen competitie gevonden')

# TODO: gebruik assert_other_http_commands_not_supported

# end of file
