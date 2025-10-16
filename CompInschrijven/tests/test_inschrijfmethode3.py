# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.definities import MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
from BasisTypen.models import BoogType
from Competitie.definities import DEEL_RK, DEEL_BK, INSCHRIJF_METHODE_3
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieSporterBoog, Kampioenschap
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompInschrijvenMethode3(E2EHelpers, TestCase):

    """ tests voor de CompInschrijven applicatie, inschrijfmethode 3 """

    test_after = ('Competitie.tests.test_tijdlijn',)

    url_aangemeld_alles = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/alles/'  # comp_pk
    url_behoefte3 = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/dagdeel-behoefte/'  # comp_pk, regio_pk
    url_behoefte3_bestand = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/dagdeel-behoefte-als-bestand/'  # comp_pk, regio_pk
    url_klassengrenzen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'
    url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/'     # comp_pk
    url_voorkeuren = '/sporter/voorkeuren/%s/'  # lid_nr

    testdata = None
    begin_jaar = 2019

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter(
                    lid_nr=lid_nr,
                    geslacht="M",
                    voornaam=voornaam,
                    achternaam="Tester",
                    email=voornaam.lower() + "@test.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self._ver)
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = Rayon.objects.get(rayon_nr=1)
        self.rayon_2 = Rayon.objects.get(rayon_nr=2)
        self.regio_101 = Regio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio_101)
        ver.save()
        self._ver = ver

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self._prep_beheerder_lid('BKO')
        self.account_rko = self._prep_beheerder_lid('RKO')
        self.account_rcl = self._prep_beheerder_lid('RCL')
        self.account_schutter = self._prep_beheerder_lid('Schutter')

        # creëer een competitie met regiocompetities
        self.assertEqual(0, Competitie.objects.count())
        competities_aanmaken(jaar=self.begin_jaar)
        # nu in fase A

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        for deelkamp in Kampioenschap.objects.filter(deel=DEEL_BK).all():
            deelkamp.functie.accounts.add(self.account_bko)
        # for

        for deelkamp in Kampioenschap.objects.filter(deel=DEEL_RK, rayon=self.rayon_2).all():
            deelkamp.functie.accounts.add(self.account_rko)
        # for

        for deelcomp in Regiocompetitie.objects.filter(regio=self.regio_101).all():
            deelcomp.functie.accounts.add(self.account_rcl)
        # for

        # maak nog een test vereniging, zonder HWL functie
        ver = Vereniging(
                    naam="Kleine Club",
                    ver_nr=1100,
                    regio=self.regio_101)
        ver.save()
        self._ver2 = ver

        # maak HWL functie aan voor deze vereniging
        hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        hwl.vereniging = ver
        hwl.save()

    def _doe_inschrijven(self, comp):

        # meld een bak leden aan voor de competitie
        self.e2e_wisselnaarrol_bb()

        # klassengrenzen vaststellen
        with self.assert_max_queries(97):
            resp = self.client.post(self.url_klassengrenzen % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        with self.assert_max_queries(97):
            resp = self.client.post(self.url_klassengrenzen % self.comp_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        # nu in fase A2

        # zet de inschrijfmethode van regio 101 op 'methode 3' (=voorkeur dagdelen)
        dagdelen = ['GN', 'ZAT', 'ZON']   # uit: DAGDEEL_AFKORTINGEN

        deelcomp = Regiocompetitie.objects.filter(regio=self.regio_101, competitie=comp)[0]
        deelcomp.inschrijf_methode = INSCHRIJF_METHODE_3
        deelcomp.toegestane_dagdelen = ",".join(dagdelen)
        deelcomp.save(update_fields=['inschrijf_methode', 'toegestane_dagdelen'])

        # zet de datum voor inschrijven op vandaag
        zet_competitie_fase_regio_inschrijven(comp)

        lid_nr = 110000
        recurve_boog_pk = BoogType.objects.get(afkorting='R').pk
        compound_boog_pk = BoogType.objects.get(afkorting='C').pk
        barebow_boog_pk = BoogType.objects.get(afkorting='BB').pk

        # doorloop de 2 verenigingen in deze regio
        for ver in Vereniging.objects.filter(regio=self.regio_101).order_by('ver_nr'):
            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = ver.functie_set.filter(rol='HWL').first()
            self.e2e_wissel_naar_functie(functie_hwl)
            self.e2e_check_rol('HWL')

            post_params = dict()

            # maak net zoveel leden aan als er dagdeel afkortingen zijn
            for lp in range(len(dagdelen)):
                lid_nr += 1
                sporter = Sporter(
                            lid_nr=lid_nr,
                            voornaam="Lid %s" % lid_nr,
                            achternaam="de Tester",
                            bij_vereniging=ver,
                            is_actief_lid=True,
                            geslacht='M',
                            geboorte_datum=datetime.date(self.begin_jaar - 19, 1, 1),  # senior,
                            sinds_datum=datetime.date(self.begin_jaar - 9, 1, 1))
                if barebow_boog_pk:
                    sporter.geboorte_datum = datetime.date(self.begin_jaar - 12, 1, 1)   # aspirant
                sporter.save()

                if barebow_boog_pk:
                    self.assertTrue(
                        sporter.bereken_wedstrijdleeftijd_wa(self.begin_jaar + 1) <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT)

                # haal de sporter voorkeuren op, zodat de sporter-boog records aangemaakt worden
                url_voorkeuren = self.url_voorkeuren % lid_nr

                # zet de recurve boog aan
                if lp == 1:
                    # zet de DT voorkeur aan voor een paar schutters
                    resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_R': 'on',
                                                             'voorkeur_eigen_blazoen': 'on'})
                    # onthoud deze sporter-boog om straks in bulk aan te melden
                    # 'lid_NNNNNN_boogtype_MM'
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'
                elif lp == 2:
                    resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_C': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, compound_boog_pk)] = 'on'
                elif barebow_boog_pk:
                    resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_BB': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, barebow_boog_pk)] = 'on'
                    barebow_boog_pk = None
                else:
                    resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                             'schiet_R': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'

                self.assert_is_redirect_not_plein(resp)         # check for success
            # for

            # schrijf in voor de competitie
            post_params['dagdeel'] = dagdelen.pop(-1)
            with self.assert_max_queries(26):
                resp = self.client.post(self.url_inschrijven % comp.pk, post_params)
            self.assert_is_redirect_not_plein(resp)         # check for success
        # for

    def test_anon(self):
        comp = Competitie.objects.first()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3_bestand % (comp.pk, self.regio_101.pk))
        self.assert403(resp)

    def test_behoefte3_18(self):
        comp = Competitie.objects.get(afstand='18')
        functie_rcl = Regiocompetitie.objects.get(competitie=comp,
                                                  regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        self._doe_inschrijven(comp)     # wisselt naar HWL functie
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode3-behoefte.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3_bestand % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        csv_file = 'ver_nr;Naam;Blazoen;Geen;Za;Zo;Totaal\r\n1000;Grote Club;60cm;0;0;1;1\r\n1000;Grote Club;Dutch Target;0;0;1;1\r\n1000;Grote Club;Dutch Target (wens);0;0;1;1\r\n1100;Kleine Club;40cm;0;1;0;1\r\n1100;Kleine Club;Dutch Target (wens);0;1;0;1\r\n-;-;Totalen;0;2;3;5\r\n-;-;-;-;-;-;-\r\n-;-;Blazoen;Geen;Za;Zo;Totaal\r\n-;-;40cm;0;1;0;1\r\n-;-;60cm;0;0;1;1\r\n-;-;Dutch Target;0;0;1;1\r\n-;-;Dutch Target (wens);0;1;1;2\r\n'
        self.assertContains(resp, csv_file, msg_prefix="(was: %s)" % resp.content)

        # creëer een beetje puinhoop
        self._ver2.regio = Regio.objects.get(pk=102)
        self._ver2.save()

        obj = RegiocompetitieSporterBoog.objects.filter(bij_vereniging=self._ver).first()
        obj.inschrijf_voorkeur_dagdeel = 'XX'
        obj.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode3-behoefte.dtl', 'design/site_layout.dtl'))

    def test_behoefte3_25(self):
        comp = Competitie.objects.filter(afstand='25').first()
        functie_rcl = Regiocompetitie.objects.get(competitie=comp, regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        self._doe_inschrijven(comp)     # wisselt naar HWL functie
        self.e2e_wissel_naar_functie(functie_rcl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode3-behoefte.dtl', 'design/site_layout.dtl'))

        # TODO: eigen_blazoen aanzetten zodat 60cm 4-spot ook gekozen wordt
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3_bestand % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        csv_file = b'ver_nr;Naam;Blazoen;Geen;Za;Zo;Totaal\r\n1000;Grote Club;60cm;0;0;3;3\r\n1100;Kleine Club;60cm;0;2;0;2\r\n-;-;Totalen;0;2;3;5\r\n-;-;-;-;-;-;-\r\n-;-;Blazoen;Geen;Za;Zo;Totaal\r\n-;-;60cm;0;2;3;5\r\n'
        self.assertContains(resp, csv_file, msg_prefix="(was: %s)" % resp.content)

        # creëer een beetje puinhoop
        self._ver2.regio = Regio.objects.get(pk=102)
        self._ver2.save()

        obj = RegiocompetitieSporterBoog.objects.filter(bij_vereniging=self._ver).first()
        obj.inschrijf_voorkeur_dagdeel = 'XX'
        obj.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte3 % (comp.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode3-behoefte.dtl', 'design/site_layout.dtl'))

        # landelijk
        url = self.url_aangemeld_alles % comp.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/lijst-aangemeld-regio.dtl', 'design/site_layout.dtl'))

    def test_bad_hwl(self):
        comp = Competitie.objects.get(afstand=18)       # let op: 25 werkt niet

        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()
        self._doe_inschrijven(comp)     # wisselt naar HWL functie

        self.e2e_wissel_naar_functie(self.functie_hwl)

        # landelijk
        zet_competitie_fase_regio_inschrijven(comp)
        comp.bepaal_fase()
        self.assertEqual(comp.fase_indiv, 'C')

        # als HWL is deze pagina niet beschikbaar
        url = self.url_behoefte3 % (999999, 101)
        resp = self.client.get(url)
        self.assert403(resp)

    def test_bad_rcl(self):
        comp = Competitie.objects.get(afstand='25')
        functie_rcl = Regiocompetitie.objects.get(competitie=comp,
                                                  regio=self.regio_101).functie

        self.e2e_login_and_pass_otp(self.account_rcl)
        self.e2e_wissel_naar_functie(functie_rcl)

        # competitie bestaat niet
        url = self.url_behoefte3 % (999999, 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_behoefte3_bestand % (999999, 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # regio bestaat niet
        url = self.url_behoefte3 % (comp.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        url = self.url_behoefte3_bestand % (comp.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        # deelcomp bestaat niet
        url = self.url_behoefte3 % (comp.pk, 100)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        url = self.url_behoefte3_bestand % (comp.pk, 100)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        # correct, maar niet inschrijfmethode 3
        url = self.url_behoefte3 % (comp.pk, 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        url = self.url_behoefte3_bestand % (comp.pk, 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')


# end of file
