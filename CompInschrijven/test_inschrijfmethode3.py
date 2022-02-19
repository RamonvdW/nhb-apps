# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
from Functie.models import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter
from Competitie.models import (Competitie, DeelCompetitie, RegioCompetitieSchutterBoog,
                               INSCHRIJF_METHODE_3, LAAG_REGIO, LAAG_RK, LAAG_BK)
from Competitie.operations import competities_aanmaken
from Competitie.test_fase import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompInschrijvenMethode3(E2EHelpers, TestCase):

    """ tests voor de CompInschrijven applicatie, inschrijfmethode 3 """

    test_after = ('Competitie.test_beheerders',)

    url_aangemeld_alles = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/alles/'  # comp_pk
    url_behoefte3 = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/dagdeel-behoefte/'  # comp_pk, regio_pk
    url_behoefte3_bestand = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/dagdeel-behoefte-als-bestand/'  # comp_pk, regio_pk

    testdata = None
    begin_jaar = 2019

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter()
        sporter.lid_nr = lid_nr
        sporter.geslacht = "M"
        sporter.voornaam = voornaam
        sporter.achternaam = "Tester"
        sporter.email = voornaam.lower() + "@nhb.test"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = self._ver
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = NhbRayon.objects.get(rayon_nr=1)
        self.rayon_2 = NhbRayon.objects.get(rayon_nr=2)
        self.regio_101 = NhbRegio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met deelcompetities
        competities_aanmaken(jaar=self.begin_jaar)
        # nu in fase A

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_BK).all():
            deelcomp.functie.accounts.add(self.account_bko)
        # for

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_RK, nhb_rayon=self.rayon_2).all():
            deelcomp.functie.accounts.add(self.account_rko)
        # for

        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_REGIO, nhb_regio=self.regio_101).all():
            deelcomp.functie.accounts.add(self.account_rcl)
        # for

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self._ver2 = ver

        # maak HWL functie aan voor deze vereniging
        hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        hwl.nhb_ver = ver
        hwl.save()

    def _doe_inschrijven(self, comp):

        url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/' % comp.pk

        # meld een bak leden aan voor de competitie
        self.e2e_wisselnaarrol_bb()

        # klassengrenzen vaststellen
        url_klassengrenzen = '/bondscompetities/%s/klassengrenzen/vaststellen/'
        with self.assert_max_queries(91):
            resp = self.client.post(url_klassengrenzen % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        with self.assert_max_queries(91):
            resp = self.client.post(url_klassengrenzen % self.comp_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        # nu in fase A2

        # zet de inschrijfmethode van regio 101 op 'methode 3', oftewel met dagdeel voorkeur
        dagdelen = ['GN', 'ZAT', 'ZON']   # uit: DAGDEEL_AFKORTINGEN

        deelcomp = DeelCompetitie.objects.filter(laag=LAAG_REGIO, nhb_regio=self.regio_101, competitie=comp)[0]
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = ",".join(dagdelen)
        deelcomp.save(update_fields=['inschrijf_methode', 'toegestane_dagdelen'])

        # zet de datum voor inschrijven op vandaag
        for comp in Competitie.objects.filter(is_afgesloten=False):
            zet_competitie_fase(comp, 'B')
        # for

        lid_nr = 110000
        recurve_boog_pk = BoogType.objects.get(afkorting='R').pk
        compound_boog_pk = BoogType.objects.get(afkorting='C').pk
        barebow_boog_pk = BoogType.objects.get(afkorting='BB').pk

        # doorloop de 2 verenigingen in deze regio
        for nhb_ver in NhbVereniging.objects.filter(regio=self.regio_101):
            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = nhb_ver.functie_set.filter(rol='HWL').all()[0]
            self.e2e_wissel_naar_functie(functie_hwl)

            post_params = dict()

            # maak net zoveel leden aan als er dagdeel afkortingen zijn
            for lp in range(len(dagdelen)):
                lid_nr += 1
                sporter = Sporter()
                sporter.lid_nr = lid_nr
                sporter.voornaam = "Lid %s" % lid_nr
                sporter.achternaam = "de Tester"
                sporter.bij_vereniging = nhb_ver
                sporter.is_actief_lid = True
                if barebow_boog_pk:
                    sporter.geboorte_datum = datetime.date(self.begin_jaar - 12, 1, 1)   # aspirant
                else:
                    sporter.geboorte_datum = datetime.date(self.begin_jaar - 19, 1, 1)   # senior
                sporter.sinds_datum = datetime.date(self.begin_jaar - 9, 1, 1)
                sporter.geslacht = 'M'
                sporter.save()

                if barebow_boog_pk:
                    self.assertTrue(sporter.bereken_wedstrijdleeftijd(self.begin_jaar + 1) <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT)

                # haal de schutter voorkeuren op, zodat de schutterboog records aangemaakt worden
                url_voorkeuren = '/sporter/voorkeuren/%s/' % lid_nr
                with self.assert_max_queries(20):
                    resp = self.client.get(url_voorkeuren)
                self.assertEqual(resp.status_code, 200)     # 200 = OK

                # zet de recurve boog aan
                if lp == 1:
                    # zet de DT voorkeur aan voor een paar schutters
                    with self.assert_max_queries(20):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_R': 'on',
                                                                 'voorkeur_eigen_blazoen': 'on'})
                    # onthoud deze schutterboog om straks in bulk aan te melden
                    # 'lid_NNNNNN_boogtype_MM'
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'
                elif lp == 2:
                    with self.assert_max_queries(20):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_C': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, compound_boog_pk)] = 'on'
                elif barebow_boog_pk:
                    with self.assert_max_queries(20):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_BB': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, barebow_boog_pk)] = 'on'
                    barebow_boog_pk = None
                else:
                    with self.assert_max_queries(20):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_R': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'

                self.assert_is_redirect_not_plein(resp)         # check for success
            # for

            # schrijf in voor de competitie
            post_params['dagdeel'] = dagdelen.pop(-1)
            with self.assert_max_queries(22):
                resp = self.client.post(url_inschrijven, post_params)
            self.assert_is_redirect_not_plein(resp)         # check for success
        # for

    def test_anon(self):
        comp = Competitie.objects.all()[0]

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3_bestand % (comp.pk, self.regio_101.pk))
        self.assert403(resp)

    def test_behoefte3_18(self):
        comp = Competitie.objects.get(afstand='18')
        functie_rcl = DeelCompetitie.objects.get(competitie=comp,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        self._doe_inschrijven(comp)     # wisselt naar HWL functie
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3_bestand % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        csv_file = 'ver_nr;Naam;Blazoen;Geen voorkeur;Zaterdag;Zondag;Totaal\r\n1000;Grote Club;60cm;0;0;1;1\r\n1000;Grote Club;Dutch Target;0;0;1;1\r\n1000;Grote Club;Dutch Target (wens);0;0;1;1\r\n1100;Kleine Club;40cm;0;1;0;1\r\n1100;Kleine Club;Dutch Target (wens);0;1;0;1\r\n-;-;Totalen;0;2;3;5\r\n-;-;-;-;-;-;-\r\n-;-;Blazoen;Geen voorkeur;Zaterdag;Zondag;Totaal\r\n-;-;40cm;0;1;0;1\r\n-;-;60cm;0;0;1;1\r\n-;-;Dutch Target;0;0;1;1\r\n-;-;Dutch Target (wens);0;1;1;2\r\n'
        self.assertContains(resp, csv_file, msg_prefix="(was: %s)" % resp.content)

        # creëer een beetje puinhoop
        self._ver2.regio = NhbRegio.objects.get(pk=102)
        self._ver2.save()

        obj = RegioCompetitieSchutterBoog.objects.filter(bij_vereniging=self._ver).all()[0]
        obj.inschrijf_voorkeur_dagdeel = 'XX'
        obj.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

    def test_behoefte3_25(self):
        comp = Competitie.objects.filter(afstand='25').all()[0]
        functie_rcl = DeelCompetitie.objects.get(competitie=comp, laag=LAAG_REGIO, nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        self._doe_inschrijven(comp)     # wisselt naar HWL functie
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

        # TODO: eigen_blazoen aanzetten zodat 60cm 4-spot ook gekozen wordt
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3_bestand % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        csv_file = 'ver_nr;Naam;Blazoen;Geen voorkeur;Zaterdag;Zondag;Totaal\r\n1000;Grote Club;60cm;0;0;3;3\r\n1100;Kleine Club;60cm;0;2;0;2\r\n-;-;Totalen;0;2;3;5\r\n-;-;-;-;-;-;-\r\n-;-;Blazoen;Geen voorkeur;Zaterdag;Zondag;Totaal\r\n-;-;60cm;0;2;3;5\r\n'
        self.assertContains(resp, csv_file, msg_prefix="(was: %s)" % resp.content)

        # creëer een beetje puinhoop
        self._ver2.regio = NhbRegio.objects.get(pk=102)
        self._ver2.save()

        obj = RegioCompetitieSchutterBoog.objects.filter(bij_vereniging=self._ver).all()[0]
        obj.inschrijf_voorkeur_dagdeel = 'XX'
        obj.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode3-behoefte.dtl', 'plein/site_layout.dtl'))

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'plein/site_layout.dtl'))

    def test_bad_hwl(self):
        comp = Competitie.objects.get(afstand=18)       # let op: 25 werkt niet

        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()
        self._doe_inschrijven(comp)     # wisselt naar HWL functie

        self.e2e_wissel_naar_functie(self.functie_hwl)

        # landelijk
        zet_competitie_fase(comp, 'C')
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'C')

        # als HWL is deze pagina niet beschikbaar
        url = self.url_behoefte3 % (999999, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

    def test_bad_rcl(self):
        comp = Competitie.objects.get(afstand='25')
        functie_rcl = DeelCompetitie.objects.get(competitie=comp,
                                                 laag=LAAG_REGIO,
                                                 nhb_regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(functie_rcl)

        # competitie bestaat niet
        url = self.url_behoefte3 % (999999, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_behoefte3_bestand % (999999, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # regio bestaat niet
        url = self.url_behoefte3 % (comp.pk, 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_behoefte3_bestand % (comp.pk, 999999)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # deelcomp bestaat niet
        url = self.url_behoefte3 % (comp.pk, 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_behoefte3_bestand % (comp.pk, 100)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        # correct, maar niet inschrijfmethode 3
        url = self.url_behoefte3 % (comp.pk, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found

        url = self.url_behoefte3_bestand % (comp.pk, 101)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found


# end of file
