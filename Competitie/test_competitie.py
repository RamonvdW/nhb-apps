# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
# from django.utils import timezone
from BasisTypen.models import BoogType, TeamWedstrijdklasse
from Functie.models import maak_functie
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Competitie.models import (Competitie, DeelCompetitie, CompetitieKlasse, CompetitieMutatie,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2, INSCHRIJF_METHODE_3,
                               DAGDEEL_AFKORTINGEN)
from Competitie.operations import (competities_aanmaken, aanvangsgemiddelden_vaststellen_voor_afstand,
                                   competitie_klassengrenzen_vaststellen)
from Competitie.test_fase import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


def maak_competities_en_zet_fase_b(startjaar=None):
    """ Competities 18m en 25m aanmaken, AG vaststellen, klassengrenzen vaststelen, instellen op fase B """

    # dit voorkomt kennis en afhandelen van achtergrondtaken in alle applicatie test suites

    # competitie aanmaken
    competities_aanmaken(startjaar)

    comp_18 = Competitie.objects.get(afstand='18')
    comp_25 = Competitie.objects.get(afstand='25')

    # aanvangsgemiddelden vaststellen
    aanvangsgemiddelden_vaststellen_voor_afstand(18)
    aanvangsgemiddelden_vaststellen_voor_afstand(25)

    # klassengrenzen vaststellen
    competitie_klassengrenzen_vaststellen(comp_18)
    competitie_klassengrenzen_vaststellen(comp_25)

    zet_competitie_fase(comp_18, 'B')
    zet_competitie_fase(comp_25, 'B')

    return comp_18, comp_25


class TestCompetitie(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie """

    test_after = ('BasisTypen', 'Functie', 'Competitie.test_fase')

    url_kies = '/bondscompetities/'
    url_overzicht = '/bondscompetities/%s/'
    url_instellingen = '/bondscompetities/instellingen-volgende-competitie/'
    url_aanmaken = '/bondscompetities/aanmaken/'
    url_ag_vaststellen_afstand = '/bondscompetities/ag-vaststellen/%s/'  # afstand
    url_klassengrenzen_vaststellen = '/bondscompetities/%s/klassengrenzen/vaststellen/'  # comp_pk
    url_klassengrenzen_tonen = '/bondscompetities/%s/klassengrenzen/tonen/'  # comp_pk

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
        # secretaris kan nog niet ingevuld worden
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
        boog_ib = BoogType.objects.get(afkorting='IB')

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
        sporterboog = SporterBoog(sporter=self.sporter_100001, boogtype=boog_ib, voor_wedstrijd=True)
        sporterboog.save()

        # (strategisch gekozen) historische data om klassengrenzen uit te bepalen
        histcomp = HistCompetitie()
        histcomp.seizoen = '2018/2019'
        histcomp.comp_type = '18'
        histcomp.klasse = 'Testcurve1'       # TODO: kan de klasse een spatie bevatten?
        histcomp.is_team = False
        histcomp.save()
        self.histcomp = histcomp

        # een ouder seizoen dat niet gebruikt moet worden
        histcomp2 = HistCompetitie()
        histcomp2.seizoen = '2017/2018'
        histcomp2.comp_type = '18'
        histcomp2.klasse = 'Testcurve2'
        histcomp2.is_team = False
        histcomp2.save()

        # record voor het volwassen lid
        rec = HistCompetitieIndividueel()
        rec.histcompetitie = histcomp
        rec.rank = 1
        rec.schutter_nr = self.sporter_100001.lid_nr
        rec.schutter_naam = self.sporter_100001.volledige_naam()
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
        rec.schutter_nr = self.sporter_100001.lid_nr
        rec.schutter_naam = self.sporter_100001.volledige_naam()
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
        rec.schutter_nr = self.sporter_100001.lid_nr
        rec.schutter_naam = self.sporter_100001.volledige_naam()
        rec.vereniging_nr = ver.ver_nr
        rec.vereniging_naam = ver.naam
        rec.boogtype = 'IB'
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
        rec.schutter_nr = self.sporter_100002.lid_nr
        rec.schutter_naam = self.sporter_100002.volledige_naam()
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
        rec.schutter_nr = self.sporter_100002.lid_nr
        rec.schutter_naam = self.sporter_100002.volledige_naam()
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
        rec.schutter_nr = 991111
        rec.schutter_naam = "Die is weg"
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
                                            schutter_nr=sporter.lid_nr,
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

    def test_instellingen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_instellingen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-instellingen-nieuwe-competitie.dtl', 'plein/site_layout.dtl'))

    def test_aanmaken(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-competities-aanmaken.dtl', 'plein/site_layout.dtl'))

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
        self.assert_template_used(resp, ('competitie/bb-competities-aanmaken.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, "Wat doe je hier?")

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        self.assertEqual(Competitie.objects.count(), 2)
        self.assertEqual(DeelCompetitie.objects.count(), 2*(1 + 4 + 16))

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

        # trigger de permissie check (want: geen competitie aangemaakt)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ag_vaststellen_afstand % '18')
        self.assert404(resp)

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
        CompetitieKlasse(competitie=comp, min_ag=25.0).save()
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
        self.assert404(resp)

        # aanmaken wordt gedaan door de achtergrondtaak, maar die draait nu niet
        aanvangsgemiddelden_vaststellen_voor_afstand(18)
        aanvangsgemiddelden_vaststellen_voor_afstand(25)

        # controleer dat er geen dubbele SporterBoog records aangemaakt zijn
        self.assertEqual(1, SporterBoog.objects.filter(sporter=self.sporter_100001, boogtype__afkorting='R').count())
        self.assertEqual(1, SporterBoog.objects.filter(sporter=self.sporter_100002, boogtype__afkorting='BB').count())
        self.assertEqual(17835, SporterBoog.objects.count())

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

        with self.assert_max_queries(32, check_duration=False):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bb-klassengrenzen-vaststellen.dtl', 'plein/site_layout.dtl'))

        # nu kunnen we met een POST de klassengrenzen vaststellen
        count = CompetitieKlasse.objects.filter(competitie=comp18, min_ag__gt=0).count()
        self.assertEqual(count, 0)
        with self.assert_max_queries(91):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)        # redirect = success
        count = CompetitieKlasse.objects.filter(competitie=comp18, min_ag__gt=0).count()
        self.assertTrue(count > 20)
        # TODO: check nog meer velden van de aangemaakte objecten

        # coverage: nog een keer vaststellen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)             # 200 = OK

        count1 = CompetitieKlasse.objects.filter(competitie=comp18).count()
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)        # redirect = success
        count2 = CompetitieKlasse.objects.filter(competitie=comp18).count()
        self.assertEqual(count1, count2)

        # coverage
        obj = CompetitieKlasse.objects.all()[0]
        self.assertTrue(str(obj) != "")
        obj.indiv = None
        obj.team = TeamWedstrijdklasse.objects.all()[0]
        self.assertTrue(str(obj) != "")

    def test_klassengrenzen_vaststellen_cornercases(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        competities_aanmaken()

        # illegale competitie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_vaststellen % 'xx')
        self.assert404(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_klassengrenzen_vaststellen % 'xx')
        self.assert404(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_tonen % 999999)
        self.assert404(resp)

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
        with self.assert_max_queries(91):
            resp = self.client.post(self.url_klassengrenzen_vaststellen % comp_18.pk)
        # s2 = timezone.now()
        # print('duration:', s2-s1)
        self.assert_is_redirect_not_plein(resp)        # redirect = success
        with self.assert_max_queries(91):
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

    def test_team(self):
        # slechts een test van een CompetitieKlasse() gekoppeld aan een TeamWedstrijdKlasse
        datum = datetime.date(year=2015, month=11, day=12)
        comp = Competitie(afstand='18', beschrijving='Test Competitie', begin_jaar=2015,
                          uiterste_datum_lid=datum,
                          begin_aanmeldingen=datum,
                          einde_aanmeldingen=datum,
                          einde_teamvorming=datum,
                          eerste_wedstrijd=datum,
                          laatst_mogelijke_wedstrijd=datum,
                          datum_klassengrenzen_rk_bk_teams=datum,
                          rk_eerste_wedstrijd=datum,
                          rk_laatste_wedstrijd=datum,
                          bk_eerste_wedstrijd=datum,
                          bk_laatste_wedstrijd=datum)
        comp.save()

        wkl = TeamWedstrijdklasse.objects.all()[0]

        obj = CompetitieKlasse(competitie=comp, team=wkl, min_ag=0.42)
        obj.save()
        self.assertTrue(wkl.beschrijving in str(obj))


# TODO: gebruik assert_other_http_commands_not_supported

# end of file
