# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.definities import INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_2, INSCHRIJF_METHODE_3, DAGDEEL_AFKORTINGEN
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse, Regiocompetitie, Kampioenschap,
                               CompetitieMutatie)
from Competitie.operations import competities_aanmaken, aanvangsgemiddelden_vaststellen_voor_afstand
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_prep, zet_competitie_fase_afsluiten
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompBeheerBB(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module BB """

    test_after = ('BasisTypen', 'Functie', 'Competitie.tests.test_overzicht')

    url_kies = '/bondscompetities/'
    url_overzicht = '/bondscompetities/%s/'
    url_overzicht_beheer = '/bondscompetities/beheer/%s/'
    url_aanmaken = '/bondscompetities/beheer/aanmaken/'
    url_instellingen = '/bondscompetities/beheer/instellingen-volgende-competitie/'
    url_ag_vaststellen_afstand = '/bondscompetities/beheer/ag-vaststellen/%s/'                  # afstand
    url_klassengrenzen_vaststellen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'  # comp_pk
    url_klassengrenzen_tonen = '/bondscompetities/%s/klassengrenzen-tonen/'                     # comp_pk_of_seizoen
    url_seizoen_afsluiten = '/bondscompetities/beheer/seizoen-afsluiten/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # deze test is afhankelijk van de standaard regio's
        self.regio_101 = regio = Regio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio)
        ver.save()

        # maak een volwassen test lid aan (komt in groep met klasse onbekend)
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="rdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        self.account_lid = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account_lid
        sporter.save()
        self.sporter_100001 = sporter

        self.functie_hwl = maak_functie('HWL test', 'HWL')
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_lid)

        # maak een jeugdlid aan (komt in BB jeugd zonder klasse onbekend)
        sporter = Sporter(
                    lid_nr=100002,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="het Testertje",
                    email="rdetestertje@gmail.not",
                    geboorte_datum=datetime.date(year=2008, month=3, day=4),
                    sinds_datum=datetime.date(year=2015, month=11, day=12),
                    bij_vereniging=ver)
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

        sporter = Sporter(
                    lid_nr=100003,
                    geslacht="V",
                    voornaam="Zus",
                    achternaam="de Testerin",
                    email="zus@gmail.not",
                    geboorte_datum=datetime.date(year=2008, month=3, day=4),
                    sinds_datum=datetime.date(year=2015, month=11, day=12),
                    bij_vereniging=ver)
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
        self.hist_seizoen = HistCompSeizoen(seizoen='2018/2019', comp_type=HISTCOMP_TYPE_18,
                                            indiv_bogen=",".join(HIST_BOGEN_DEFAULT))
        self.hist_seizoen.save()

        # een ouder seizoen dat niet gebruikt moet worden
        hist_seizoen2 = HistCompSeizoen(seizoen='2017/2018', comp_type=HISTCOMP_TYPE_18,
                                        indiv_bogen=",".join(HIST_BOGEN_DEFAULT))
        hist_seizoen2.save()

        # record voor het volwassen lid
        rec = HistCompRegioIndiv(
                    seizoen=self.hist_seizoen,
                    rank=1,
                    sporter_lid_nr=self.sporter_100001.lid_nr,
                    sporter_naam=self.sporter_100001.volledige_naam(),
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam=ver.naam,
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

        # nog een record voor het volwassen lid
        rec = HistCompRegioIndiv(
                    seizoen=hist_seizoen2,
                    rank=1,
                    sporter_lid_nr=self.sporter_100001.lid_nr,
                    sporter_naam=self.sporter_100001.volledige_naam(),
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam=ver.naam,
                    boogtype='R',
                    score1=11,
                    score2=21,
                    score3=31,
                    score4=41,
                    score5=51,
                    score6=61,
                    score7=71,
                    totaal=81,
                    gemiddelde=6.12)
        rec.save()

        # nog een record voor het volwassen lid
        rec = HistCompRegioIndiv(
                    seizoen=self.hist_seizoen,
                    rank=100,
                    sporter_lid_nr=self.sporter_100001.lid_nr,
                    sporter_naam=self.sporter_100001.volledige_naam(),
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam=ver.naam,
                    boogtype='TR',
                    score1=11,
                    score2=21,
                    score3=31,
                    score4=41,
                    score5=51,
                    score6=61,
                    score7=71,
                    totaal=81,
                    gemiddelde=6.12)
        rec.save()

        # maak een record aan zonder eindgemiddelde
        rec = HistCompRegioIndiv(
                    seizoen=self.hist_seizoen,
                    rank=1,
                    sporter_lid_nr=self.sporter_100002.lid_nr,
                    sporter_naam=self.sporter_100002.volledige_naam(),
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam=ver.naam,
                    boogtype='C',
                    score1=0,
                    score2=0,
                    score3=0,
                    score4=0,
                    score5=0,
                    score6=0,
                    score7=0,
                    totaal=0,
                    gemiddelde=0.0)
        rec.save()

        # record voor het jeugdlid
        rec = HistCompRegioIndiv(
                    seizoen=self.hist_seizoen,
                    rank=1,
                    sporter_lid_nr=self.sporter_100002.lid_nr,
                    sporter_naam=self.sporter_100002.volledige_naam(),
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam=ver.naam,
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

        # maak een record aan voor iemand die geen lid meer is
        rec = HistCompRegioIndiv(
                    seizoen=self.hist_seizoen,
                    rank=1,
                    sporter_lid_nr=991111,
                    sporter_naam="Die is weg",
                    vereniging_nr=ver.ver_nr,
                    vereniging_naam=ver.naam,
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

            rec = HistCompRegioIndiv(
                        seizoen=self.hist_seizoen,
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
        HistCompRegioIndiv.objects.bulk_create(records)

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'design/site_layout.dtl'))

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
        self.assert_template_used(resp, ('compbeheer/bb-instellingen-nieuwe-competitie.dtl', 'design/site_layout.dtl'))

    def test_aanmaken(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmaken)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-competities-aanmaken.dtl', 'design/site_layout.dtl'))

        # gebruik een post om de competitie aan te laten maken
        # geen parameters nodig
        self.assertEqual(Competitie.objects.count(), 0)
        self.assertEqual(Regiocompetitie.objects.count(), 0)
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
        self.assert_template_used(resp, ('compbeheer/bb-competities-aanmaken.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, "Wat doe je hier?")

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_aanmaken)
        self.assert_is_redirect(resp, self.url_kies)

        self.assertEqual(Competitie.objects.count(), 2)
        self.assertEqual(Regiocompetitie.objects.count(), 2 * 16)
        self.assertEqual(Kampioenschap.objects.count(), 2 * 5)

    def test_regio_settings_overnemen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.assertEqual(Regiocompetitie.objects.count(), 0)

        # maak een competitie aan
        competities_aanmaken(jaar=2019)

        dagdelen_105_18 = "%s,%s,%s" % (DAGDEEL_AFKORTINGEN[0], DAGDEEL_AFKORTINGEN[1], DAGDEEL_AFKORTINGEN[2])
        dagdelen_105_25 = "%s,%s,%s" % (DAGDEEL_AFKORTINGEN[3], DAGDEEL_AFKORTINGEN[4], DAGDEEL_AFKORTINGEN[0])

        # pas regio-instellingen aan
        deelcomp = Regiocompetitie.objects.get(
                                competitie__afstand=18,
                                regio__regio_nr=101)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        deelcomp.save()

        deelcomp = Regiocompetitie.objects.get(
                                competitie__afstand=18,
                                regio__regio_nr=105)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = dagdelen_105_18
        deelcomp.save()

        deelcomp = Regiocompetitie.objects.get(
                                competitie__afstand=25,
                                regio__regio_nr=105)
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = dagdelen_105_25
        deelcomp.save()

        # maak opnieuw een competitie aan
        competities_aanmaken(jaar=2020)

        # controleer dat de settings overgenomen zijn
        for deelcomp in (Regiocompetitie
                         .objects
                         .select_related('competitie', 'regio')
                         .filter(regio__regio_nr=101)):
            if deelcomp.competitie.is_indoor():
                self.assertEqual(deelcomp.inschrijf_methode, INSCHRIJF_METHODE_1)
            else:
                self.assertEqual(deelcomp.inschrijf_methode, INSCHRIJF_METHODE_2)
        # for

        for deelcomp in (Regiocompetitie
                         .objects
                         .select_related('competitie', 'regio')
                         .filter(regio__regio_nr=105)):
            self.assertEqual(deelcomp.inschrijf_methode, INSCHRIJF_METHODE_3)
            if deelcomp.competitie.is_indoor():
                self.assertEqual(deelcomp.toegestane_dagdelen, dagdelen_105_18)
            else:
                self.assertEqual(deelcomp.toegestane_dagdelen, dagdelen_105_25)
        # for

    def test_check_krijgt_scheids(self):
        # maak een competitie aan
        competities_aanmaken(jaar=2020)
        comp_18 = Competitie.objects.filter(afstand=18).first()
        comp_25 = Competitie.objects.filter(afstand=25).first()

        # Indoor krijgt scheidsrechter op RK voor de 1e klasse R, C, BB
        for volgorde in (1100,   # R kl 1
                         1110,   # R O21 kl 1
                         1200,   # C kl 1
                         1300):  # BB kl 1
            klasse = CompetitieIndivKlasse.objects.get(competitie=comp_18, volgorde=volgorde)
            self.assertTrue(klasse.krijgt_scheids_rk, msg=str(klasse))
        # for

        # Indoor individueel krijgt geen scheidsrechter op RK voor de >1e klasse en voor TR, LB kl 1
        for volgorde in (1101,   # R kl 2
                         1105,   # R kl 6
                         1111,   # R O21 kl 2
                         1201,   # C kl 2
                         1301,   # BB kl 2
                         1400,   # TR kl 1
                         1401,   # TR kl 2
                         1500):  # LB kl 1
            klasse = CompetitieIndivKlasse.objects.get(competitie=comp_18, volgorde=volgorde)
            self.assertFalse(klasse.krijgt_scheids_rk, msg=str(klasse))
        # for

        # Indoor teams krijgt scheidsrechter op RK voor ERE klasse R, C, BB
        # (100 + is voor RK/BK-specifieke klassen)
        for volgorde in (100 + 15,   # R kl ERE
                         100 + 20,   # C kl ERE
                         100 + 31):  # BB kl ERE
            klasse = CompetitieTeamKlasse.objects.get(competitie=comp_18, volgorde=volgorde)
            self.assertTrue(klasse.krijgt_scheids_rk, msg=str(klasse))
        # for

        # Indoor teams krijgt geen scheidsrechter op RK voor TR, LB en voor alle lagere klassen dan ERE
        # (100 + is voor RK/BK-specifieke klassen)
        for volgorde in (100 + 41,   # TR kl ERE
                         100 + 50,   # LB kl ERE
                         100 + 21,   # C kl A
                         100 + 19):  # R kl D
            klasse = CompetitieTeamKlasse.objects.get(competitie=comp_18, volgorde=volgorde)
            self.assertFalse(klasse.krijgt_scheids_rk, msg=str(klasse))
        # for

        # Indoor individueel krijgt scheidsrechter op BK voor alle klassen en boogtypen
        count = CompetitieIndivKlasse.objects.filter(competitie=comp_18, krijgt_scheids_bk=True).count()
        self.assertEqual(count, 25)

        # 25m1pijl krijgt nergens een scheids op het RK of BK
        count = CompetitieIndivKlasse.objects.filter(competitie=comp_25, krijgt_scheids_rk=True).count()
        self.assertEqual(count, 0)

        count = CompetitieIndivKlasse.objects.filter(competitie=comp_25, krijgt_scheids_bk=True).count()
        self.assertEqual(count, 0)

        count = CompetitieTeamKlasse.objects.filter(competitie=comp_25, krijgt_scheids_rk=True).count()
        self.assertEqual(count, 0)

        count = CompetitieTeamKlasse.objects.filter(competitie=comp_25, krijgt_scheids_bk=True).count()
        self.assertEqual(count, 0)

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
        self.assert404(resp, 'Geen competitie in de juiste fase')

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
            resp = self.client.get(self.url_overzicht_beheer % comp.pk)
        urls = self.extract_all_urls(resp)
        self.assertTrue(self.url_ag_vaststellen_afstand % comp.afstand in urls)
        self.assertNotContains(resp, "laatst gedaan op")

        # verander de fase van de 25m competitie zodat we verschillen hebben
        comp = Competitie.objects.get(afstand=25, is_afgesloten=False)
        CompetitieIndivKlasse(competitie=comp,
                              volgorde=1,
                              min_ag=25.0,
                              boogtype=self.sporterboog_100002.boogtype).save()
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
        self.assertEqual(14354, SporterBoog.objects.count())

        # controleer dat het "ag vaststellen" kaartje er nog steeds is
        # dit keer met de "voor het laatst gedaan" notitie
        comp = Competitie.objects.get(afstand=18, is_afgesloten=False)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht_beheer % comp.pk)
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertTrue(self.url_ag_vaststellen_afstand % 18 in urls)
        self.assertContains(resp, "laatst gedaan op")

    def test_ag_vaststellen_cornercases(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # maak de competities aan - de voorwaarde om AG's vast te stellen
        competities_aanmaken()

        # geen HistCompIndividueel
        HistCompRegioIndiv.objects.all().delete()

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
        HistCompSeizoen.objects.all().delete()

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
        self.assert_template_used(resp, ('compbeheer/bb-klassengrenzen-vaststellen.dtl', 'design/site_layout.dtl'))

        # nu kunnen we met een POST de klassengrenzen vaststellen
        count = CompetitieIndivKlasse.objects.filter(competitie=comp18, min_ag__gt=0).count()
        self.assertEqual(count, 0)
        with self.assert_max_queries(97):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)        # redirect = success
        count = CompetitieIndivKlasse.objects.filter(competitie=comp18, min_ag__gt=0).count()
        self.assertTrue(count > 20)
        # FUTURE: check nog meer velden van de aangemaakte objecten

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
        obj = CompetitieIndivKlasse.objects.filter(is_ook_voor_rk_bk=False)[0]
        self.assertTrue(str(obj) != "")
        obj = CompetitieIndivKlasse.objects.filter(is_ook_voor_rk_bk=True)[0]
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
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/bestaat-niet.dtl', 'design/site_layout.dtl'))

    def test_klassengrenzen_tonen(self):
        # competitie opstarten
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # maak de competities aan
        competities_aanmaken()
        comp_18 = Competitie.objects.filter(afstand=18).first()
        comp_25 = Competitie.objects.filter(afstand=25).first()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_tonen % comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassengrenzen-tonen.dtl', 'design/site_layout.dtl'))
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
        zet_competitie_fase_regio_prep(comp_18)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'design/site_layout.dtl'))

        self.e2e_logout()

        # kies pagina ophalen als bezoeker
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'design/site_layout.dtl'))

        # nog een keer
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_tonen % comp_25.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassengrenzen-tonen.dtl', 'design/site_layout.dtl'))
        self.assertNotContains(resp, ' zijn nog niet vastgesteld')
        self.assertNotContains(resp, 'De klassengrenzen voor de ')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_klassengrenzen_tonen % comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/klassengrenzen-tonen.dtl', 'design/site_layout.dtl'))
        self.assertNotContains(resp, ' zijn nog niet vastgesteld')
        self.assertNotContains(resp, 'De klassengrenzen voor de ')

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
        self.assert_template_used(resp, ('compbeheer/bb-seizoen-afsluiten.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_seizoen_afsluiten)
        self.assert404(resp, 'Alle competities nog niet in fase Q')

        # maak een HistComp aan die straks doorgezet gaat worden
        hist = HistCompSeizoen(
                        seizoen='2019/2020',
                        is_openbaar=False,
                        comp_type=HISTCOMP_TYPE_18,
                        indiv_bogen=",".join(HIST_BOGEN_DEFAULT))
        hist.save()

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        # fase Q: alle BK's afgesloten
        zet_competitie_fase_afsluiten(self.comp_18)
        zet_competitie_fase_afsluiten(self.comp_25)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_seizoen_afsluiten)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bb-seizoen-afsluiten.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_seizoen_afsluiten)
        self.assert_is_redirect(resp, '/bondscompetities/')

        hist = HistCompSeizoen.objects.get(pk=hist.pk)
        self.assertTrue(hist.is_openbaar)

        # corner case: verwijder alle competitie
        Competitie.objects.all().delete()

        resp = self.client.get(self.url_seizoen_afsluiten)
        self.assert404(resp, 'Geen competitie gevonden')

        resp = self.client.post(self.url_seizoen_afsluiten)
        self.assert404(resp, 'Geen competitie gevonden')


# TODO: gebruik assert_other_http_commands_not_supported

# end of file
