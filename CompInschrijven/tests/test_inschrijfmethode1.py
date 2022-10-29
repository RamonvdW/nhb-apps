# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, DeelCompetitie, DeelcompetitieRonde, CompetitieMatch,
                               INSCHRIJF_METHODE_1, LAAG_REGIO, LAAG_RK, LAAG_BK)
from Competitie.operations import competities_aanmaken
from Competitie.tests.test_fase import zet_competitie_fase
from Functie.operations import maak_functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbVereniging
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestCompInschrijvenMethode1(E2EHelpers, TestCase):

    """ tests voor de CompInschrijven applicatie, inschrijfmethode 1 """

    test_after = ('Competitie.tests.test_beheerders',)

    url_planning_regio = '/bondscompetities/regio/planning/%s/'                                         # deelcomp_pk
    url_planning_regio_ronde_methode1 = '/bondscompetities/regio/planning/regio-wedstrijden/%s/'        # ronde_pk
    url_wijzig_wedstrijd = '/bondscompetities/regio/planning/wedstrijd/wijzig/%s/'                      # match_pk
    url_behoefte1 = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/gemaakte-keuzes/'    # comp_pk, regio_pk
    url_behoefte1_bestand = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/gemaakte-keuzes-als-bestand/'  # comp_pk, regio_pk

    testdata = None

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
        competities_aanmaken(jaar=2019)
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

        self.deelcomp = DeelCompetitie.objects.filter(competitie=self.comp_18,
                                                      laag=LAAG_REGIO,
                                                      nhb_regio=self.regio_101)[0]

        self.functie_rcl101_18 = DeelCompetitie.objects.get(competitie=self.comp_18,
                                                            laag=LAAG_REGIO,
                                                            nhb_regio=self.regio_101).functie

        # maak nog een test vereniging, zonder HWL functie
        ver = NhbVereniging()
        ver.naam = "Kleine Club"
        ver.ver_nr = "1100"
        ver.regio = self.regio_101
        ver.save()
        self._ver2 = ver

        # maak HWL functie aan voor deze vereniging
        hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        hwl.nhb_ver = ver
        hwl.save()

        self._competitie_instellingen()
        self._maak_wedstrijden()

    def _competitie_instellingen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        # klassengrenzen vaststellen
        url_klassengrenzen = '/bondscompetities/%s/klassengrenzen/vaststellen/'
        with self.assert_max_queries(97):
            resp = self.client.post(url_klassengrenzen % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        with self.assert_max_queries(97):
            resp = self.client.post(url_klassengrenzen % self.comp_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        # nu in fase A2

        # zet de inschrijfmethode van regio 101 op 'methode 1', oftewel met keuze wedstrijden
        self.deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp.save(update_fields=['inschrijf_methode'])

        # zet de datum voor inschrijven op vandaag
        for comp in Competitie.objects.filter(is_afgesloten=False):
            zet_competitie_fase(comp, 'B')
        # for

    def _maak_wedstrijden(self):
        # wissen naar RCL rol
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # maak wedstrijden 1 voor inschrijfmethode 1
        # haal de (lege) planning op. Dit maakt ook meteen de enige ronde aan
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_planning_regio % self.deelcomp.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagregio/planning-regio-methode1.dtl', 'plein/site_layout.dtl'))

        ronde_pk = DeelcompetitieRonde.objects.filter(deelcompetitie=self.deelcomp)[0].pk
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk

        # maak 5 wedstrijden aan
        self.assertEqual(CompetitieMatch.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(url_ronde)
        self.assert_is_redirect_not_plein(resp)
        self.assertTrue(self.url_wijzig_wedstrijd[:-3] in resp.url)     # [:-3] cuts off %s/
        self.assertEqual(CompetitieMatch.objects.count(), 1)

        self.client.post(url_ronde)
        self.client.post(url_ronde)
        self.client.post(url_ronde)
        self.client.post(url_ronde)

        self.assertEqual(CompetitieMatch.objects.count(), 5)

        # zet de wedstrijden op de 15 van elke maand
        self.match_pks = list()
        maand = 7
        for match in CompetitieMatch.objects.all():
            self.match_pks.append(match.pk)

            match.datum_wanneer = '2019-%s-15' % maand
            match.tijd_begin_wedstrijd = '19:00'
            match.vereniging = self._ver
            match.save(update_fields=['datum_wanneer', 'tijd_begin_wedstrijd', 'vereniging'])

            maand += 1
        # for

    def _doe_inschrijven(self, comp):
        # maak leden aan voor de tests
        url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/' % comp.pk

        # wissel naar HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)

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

            # maak 5 leden aan
            for lp in range(5):
                lid_nr += 1
                sporter = Sporter()
                sporter.lid_nr = lid_nr
                sporter.voornaam = "Lid %s" % lid_nr
                sporter.achternaam = "de Tester"
                sporter.bij_vereniging = nhb_ver
                sporter.is_actief_lid = True
                if barebow_boog_pk:
                    sporter.geboorte_datum = datetime.date(2019-12, 1, 1)   # aspirant
                else:
                    sporter.geboorte_datum = datetime.date(2000, 1, 1)      # senior
                sporter.sinds_datum = datetime.date(2010, 1, 1)
                sporter.geslacht = 'M'
                sporter.save()

                # haal de schutter voorkeuren op, zodat de schutterboog records aangemaakt worden
                url_voorkeuren = '/sporter/voorkeuren/%s/' % lid_nr
                url_success = '/vereniging/leden-voorkeuren/'
                with self.assert_max_queries(20):
                    resp = self.client.get(url_voorkeuren)
                self.assertEqual(resp.status_code, 200)     # 200 = OK

                # zet de recurve boog aan
                if lp == 1:
                    # zet de DT voorkeur aan voor een paar schutters
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_R': 'on',
                                                                 'voorkeur_eigen_blazoen': 'on'})
                    # onthoud deze schutterboog om straks in bulk aan te melden
                    # 'lid_NNNNNN_boogtype_MM'
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'
                elif lp == 2:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_C': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, compound_boog_pk)] = 'on'
                elif barebow_boog_pk:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_BB': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, barebow_boog_pk)] = 'on'
                    barebow_boog_pk = None
                else:
                    with self.assert_max_queries(25):
                        resp = self.client.post(url_voorkeuren, {'sporter_pk': lid_nr,
                                                                 'schiet_R': 'on'})
                    post_params['lid_%s_boogtype_%s' % (lid_nr, recurve_boog_pk)] = 'on'

                self.assert_is_redirect(resp, url_success)  # redirect = succes

            # for

            # schrijf deze leden met in 4 van de 5 wedstrijden
            for pk in self.match_pks[1:]:
                post_params['wedstrijd_%s' % pk] = 'on'
            # for

            # schrijf in voor de competitie
            with self.assert_max_queries(56):
                resp = self.client.post(url_inschrijven, post_params)
            self.assert_is_redirect_not_plein(resp)         # check for success
        # for

    def test_anon(self):
        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte1 % (self.comp_18.pk, self.regio_101.pk))
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte1_bestand % (self.comp_18.pk, self.regio_101.pk))
        self.assert403(resp)

    def test_geen_keuzes(self):
        CompetitieMatch.objects.all().delete()

        # haal het lege overzicht op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte1 % (self.comp_18.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode1-behoefte.dtl', 'plein/site_layout.dtl'))

        self.assertContains(resp, 'Nog geen keuzes gemaakt')

    def test_behoefte1(self):
        # overzicht met gekozen wedstrijden voor inschrijfmethode 1, ook als bestand
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # haal het lege overzicht op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte1 % (self.comp_18.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode1-behoefte.dtl', 'plein/site_layout.dtl'))

        # schrijf een aantal sporters in
        self.e2e_wisselnaarrol_bb()
        self._doe_inschrijven(self.comp_18)     # wisselt naar HWL functie
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_behoefte1 % (self.comp_18.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode1-behoefte.dtl', 'plein/site_layout.dtl'))
        # 0 keer de eerste keuze
        self.assertContains(resp, '<td>maandag 15 juli 2019 om 19:00</td><td>[1000] Grote Club</td><td class="center">0</td>')
        # 10 keer de tweede (en overige) keuzes
        self.assertContains(resp, '<td>donderdag 15 augustus 2019 om 19:00</td><td>[1000] Grote Club</td><td class="center">10</td>')

        with self.assert_max_queries(44):       # TODO: probeer omlaag te krijgen
            resp = self.client.get(self.url_behoefte1_bestand % (self.comp_18.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        csv_file = 'Nummer;Wedstrijd;Locatie;Blazoenen:;40cm;DT;DT wens;60cm\r\n'
        csv_file += '1;maandag 15 juli 2019 om 19:00;[1000] Grote Club;;0;0;0;0\r\n'
        csv_file += '2;donderdag 15 augustus 2019 om 19:00;[1000] Grote Club;;5;2;2;1\r\n'
        csv_file += '3;zondag 15 september 2019 om 19:00;[1000] Grote Club;;5;2;2;1\r\n'
        csv_file += '4;dinsdag 15 oktober 2019 om 19:00;[1000] Grote Club;;5;2;2;1\r\n'
        csv_file += '5;vrijdag 15 november 2019 om 19:00;[1000] Grote Club;;5;2;2;1\r\n'
        csv_file += '\r\nBondsnummer;Sporter;Vereniging;Wedstrijdklasse (individueel);1;2;3;4;5\r\n'
        csv_file += '110001;Lid 110001 de Tester;[1000] Grote Club;Barebow Onder 14 Jongens;;X;X;X;X\r\n'
        csv_file += '110002;Lid 110002 de Tester;[1000] Grote Club;Recurve Onder 21 klasse onbekend;;X;X;X;X\r\n'
        csv_file += '110003;Lid 110003 de Tester;[1000] Grote Club;Compound Onder 21 klasse onbekend;;X;X;X;X\r\n'
        csv_file += '110004;Lid 110004 de Tester;[1000] Grote Club;Recurve Onder 21 klasse onbekend;;X;X;X;X\r\n'
        csv_file += '110005;Lid 110005 de Tester;[1000] Grote Club;Recurve Onder 21 klasse onbekend;;X;X;X;X\r\n'
        csv_file += '110006;Lid 110006 de Tester;[1100] Kleine Club;Recurve Onder 21 klasse onbekend;;X;X;X;X\r\n'
        csv_file += '110007;Lid 110007 de Tester;[1100] Kleine Club;Recurve Onder 21 klasse onbekend;;X;X;X;X\r\n'
        csv_file += '110008;Lid 110008 de Tester;[1100] Kleine Club;Compound Onder 21 klasse onbekend;;X;X;X;X\r\n'
        csv_file += '110009;Lid 110009 de Tester;[1100] Kleine Club;Recurve Onder 21 klasse onbekend;;X;X;X;X\r\n'
        csv_file += '110010;Lid 110010 de Tester;[1100] Kleine Club;Recurve Onder 21 klasse onbekend;;X;X;X;X\r\n'
        self.assertContains(resp, csv_file, msg_prefix="(was: %s)" % resp.content)

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
        url = self.url_behoefte1 % (999999, 101)
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
        url = self.url_behoefte1 % (999999, 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_behoefte1_bestand % (999999, 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # regio bestaat niet
        url = self.url_behoefte1 % (comp.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Regio niet gevonden')

        url = self.url_behoefte1_bestand % (comp.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Regio niet gevonden')

        # deelcomp bestaat niet
        url = self.url_behoefte1 % (comp.pk, 100)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_behoefte1_bestand % (comp.pk, 100)
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')

        # correct, maar niet inschrijfmethode 3
        url = self.url_behoefte1 % (comp.pk, 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde inschrijfmethode')

        url = self.url_behoefte1_bestand % (comp.pk, 101)
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde inschrijfmethode')

# end of file
