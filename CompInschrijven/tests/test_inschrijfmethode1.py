# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.definities import DEEL_RK, DEEL_BK, INSCHRIJF_METHODE_1
from Competitie.models import Competitie, CompetitieMatch, Regiocompetitie, RegiocompetitieRonde, Kampioenschap
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio, Cluster
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompInschrijvenMethode1(E2EHelpers, TestCase):

    """ tests voor de CompInschrijven applicatie, inschrijfmethode 1 """

    test_after = ('Competitie.tests.test_tijdlijn',)

    url_planning_regio = '/bondscompetities/regio/planning/%s/'                                         # deelcomp_pk
    url_planning_regio_ronde_methode1 = '/bondscompetities/regio/planning/regio-wedstrijden/%s/'        # ronde_pk
    url_wijzig_wedstrijd = '/bondscompetities/regio/planning/wedstrijd/wijzig/%s/'                      # match_pk
    url_behoefte1 = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/gemaakte-keuzes/'    # comp_pk, regio_pk
    url_behoefte1_bestand = '/bondscompetities/deelnemen/%s/lijst-regiocompetitie/regio-%s/gemaakte-keuzes-als-bestand/'  # comp_pk, regio_pk
    url_klassengrenzen = '/bondscompetities/beheer/%s/klassengrenzen-vaststellen/'
    url_inschrijven = '/bondscompetities/deelnemen/leden-aanmelden/%s/'         # comp.pk
    url_voorkeuren = '/sporter/voorkeuren/%s/'  # lid_nr
    url_success = '/vereniging/leden-voorkeuren/'

    testdata = None

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
        self.cluster_101a = Cluster.objects.create(regio=self.regio_101, letter='A', naam='Cluster 101a', gebruik='18')
        self.cluster_101b = Cluster.objects.create(regio=self.regio_101, letter='B', naam='Cluster 101b', gebruik='18')

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio_101)
        ver.save()
        ver.clusters.add(self.cluster_101a)
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
        competities_aanmaken(jaar=2019)
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

        self.deelcomp = Regiocompetitie.objects.filter(competitie=self.comp_18,
                                                       regio=self.regio_101)[0]

        self.functie_rcl101_18 = Regiocompetitie.objects.get(competitie=self.comp_18,
                                                             regio=self.regio_101).functie

        # maak nog een test vereniging, zonder HWL functie
        ver2 = Vereniging(
                    naam="Kleine Club",
                    ver_nr=1100,
                    regio=self.regio_101)
        ver2.save()
        ver2.clusters.add(self.cluster_101b)
        self._ver2 = ver2

        # maak HWL functie aan voor deze vereniging
        hwl = maak_functie("HWL Vereniging %s" % ver2.ver_nr, "HWL")
        hwl.vereniging = ver2
        hwl.save()

        self._competitie_instellingen()
        self._maak_wedstrijden()

    def _competitie_instellingen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)        # geen account_hwl
        self.e2e_wisselnaarrol_bb()

        # klassengrenzen vaststellen
        with self.assert_max_queries(97):
            resp = self.client.post(self.url_klassengrenzen % self.comp_18.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        with self.assert_max_queries(97):
            resp = self.client.post(self.url_klassengrenzen % self.comp_25.pk)
        self.assert_is_redirect_not_plein(resp)  # check for success
        # nu in fase A2

        # zet de inschrijfmethode van regio 101 op 'methode 1', oftewel met keuze wedstrijden
        self.deelcomp.inschrijf_methode = INSCHRIJF_METHODE_1
        self.deelcomp.save(update_fields=['inschrijf_methode'])

        # zet de datum voor inschrijven op vandaag
        for comp in Competitie.objects.filter(is_afgesloten=False):
            zet_competitie_fase_regio_inschrijven(comp)
        # for

    def _maak_wedstrijden(self):
        # wissen naar RCL rol
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # doe een POST om de rondes van inschrijfmethode1 aan te maken
        # 2 cluster-specifieke rondes + 1 niet-cluster ronde
        url = self.url_planning_regio % self.deelcomp.pk
        self.assertEqual(RegiocompetitieRonde.objects.count(), 0)
        with self.assert_max_queries(23):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)
        self.assertEqual(RegiocompetitieRonde.objects.count(), 3)

        ronde_pk = (RegiocompetitieRonde
                    .objects
                    .filter(regiocompetitie=self.deelcomp,
                            cluster=self.cluster_101a)
                    .first()).pk
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk

        # maak 1e keus wedstrijden voor inschrijfmethode 1
        # maak 5 wedstrijden aan voor de vereniging in cluster 101a

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

        # maak 2e keus wedstrijden voor inschrijfmethode 1
        # maak 4 wedstrijden aan voor de vereniging in cluster 101b

        ronde_pk = (RegiocompetitieRonde
                    .objects
                    .filter(regiocompetitie=self.deelcomp,
                            cluster=self.cluster_101b)
                    .first()).pk
        url_ronde = self.url_planning_regio_ronde_methode1 % ronde_pk

        with self.assert_max_queries(20):
            resp = self.client.post(url_ronde)
        self.assert_is_redirect_not_plein(resp)
        self.assertTrue(self.url_wijzig_wedstrijd[:-3] in resp.url)     # [:-3] cuts off %s/
        self.client.post(url_ronde)
        self.client.post(url_ronde)
        self.client.post(url_ronde)

        # zet de nieuwe wedstrijden op de 17 van elke maand en vereniging 2
        maand = 7
        for match in CompetitieMatch.objects.exclude(pk__in=self.match_pks):
            match.datum_wanneer = '2019-%s-17' % maand
            match.tijd_begin_wedstrijd = '19:00'
            match.vereniging = self._ver2
            match.save(update_fields=['datum_wanneer', 'tijd_begin_wedstrijd', 'vereniging'])

            maand += 1
        # for

    def _doe_inschrijven(self, comp):
        # maak leden aan voor de tests
        url_inschrijven = self.url_inschrijven % comp.pk

        # wissel naar HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)

        lid_nr = 110000
        recurve_boog_pk = BoogType.objects.get(afkorting='R').pk
        compound_boog_pk = BoogType.objects.get(afkorting='C').pk
        barebow_boog_pk = BoogType.objects.get(afkorting='BB').pk

        # doorloop de 2 verenigingen in deze regio
        for ver in Vereniging.objects.filter(regio=self.regio_101):
            # wordt HWL om voorkeuren aan te kunnen passen en in te kunnen schrijven
            functie_hwl = ver.functie_set.filter(rol='HWL').first()
            self.e2e_wissel_naar_functie(functie_hwl)

            post_params = dict()

            # maak 5 leden aan
            for lp in range(5):
                lid_nr += 1
                sporter = Sporter(
                            lid_nr=lid_nr,
                            voornaam="Lid %s" % lid_nr,
                            achternaam="de Tester",
                            bij_vereniging=ver,
                            is_actief_lid=True,
                            geslacht='M',
                            geboorte_datum=datetime.date(2000, 1, 1),  # senior
                            sinds_datum=datetime.date(2010, 1, 1))
                if barebow_boog_pk:
                    sporter.geboorte_datum = datetime.date(2019-12, 1, 1)   # aspirant
                sporter.save()

                # haal de sporter voorkeuren op, zodat de sporter-boog records aangemaakt worden
                url_voorkeuren = self.url_voorkeuren % lid_nr
                with self.assert_max_queries(20):
                    resp = self.client.get(url_voorkeuren)
                self.assertEqual(resp.status_code, 200)     # 200 = OK

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

                self.assert_is_redirect(resp, self.url_success)  # redirect = succes

            # for

            # schrijf deze leden met in 4 van de 5 wedstrijden
            for pk in self.match_pks[1:]:
                post_params['wedstrijd_%s' % pk] = 'on'
            # for

            # schrijf in voor de competitie
            with self.assert_max_queries(53):
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
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode1-behoefte.dtl', 'design/site_layout.dtl'))

        self.assertContains(resp, 'Nog geen keuzes gemaakt')

    def test_behoefte1(self):
        # overzicht met gekozen wedstrijden voor inschrijfmethode 1, ook als bestand
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        # haal het lege overzicht op
        with self.assert_max_queries(22):
            resp = self.client.get(self.url_behoefte1 % (self.comp_18.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode1-behoefte.dtl', 'design/site_layout.dtl'))

        # schrijf een aantal sporters in
        self.e2e_wisselnaarrol_bb()
        self._doe_inschrijven(self.comp_18)     # wisselt naar HWL functie
        self.e2e_wissel_naar_functie(self.functie_rcl101_18)

        with self.assert_max_queries(26):
            resp = self.client.get(self.url_behoefte1 % (self.comp_18.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        html = self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compinschrijven/inschrijfmethode1-behoefte.dtl', 'design/site_layout.dtl'))
        # 0 keer de eerste keuze
        self.assertIn('<td>maandag 15 juli 2019 om 19:00</td><td>[1000] Grote Club</td><td class="center">0</td>', html)
        # 10 keer de tweede (en overige) keuzes
        self.assertIn('<td>donderdag 15 augustus 2019 om 19:00</td><td>[1000] Grote Club</td><td class="center">10</td>', html)

        with self.assert_max_queries(44):       # TODO: probeer omlaag te krijgen
            resp = self.client.get(self.url_behoefte1_bestand % (self.comp_18.pk, self.regio_101.pk))
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        csv_file = 'Nummer;Wedstrijd;Locatie;Blazoenen:;40cm;DT;DT wens;60cm\r\n'
        csv_file += '1;maandag 15 juli 2019 om 19:00;[1000] Grote Club;;0;0;0;0\r\n'
        csv_file += '2;woensdag 17 juli 2019 om 19:00;[1100] Kleine Club;;0;0;0;0\r\n'
        csv_file += '3;donderdag 15 augustus 2019 om 19:00;[1000] Grote Club;;5;2;2;1\r\n'
        csv_file += '4;zaterdag 17 augustus 2019 om 19:00;[1100] Kleine Club;;0;0;0;0\r\n'
        csv_file += '5;zondag 15 september 2019 om 19:00;[1000] Grote Club;;5;2;2;1\r\n'
        csv_file += '6;dinsdag 17 september 2019 om 19:00;[1100] Kleine Club;;0;0;0;0\r\n'
        csv_file += '7;dinsdag 15 oktober 2019 om 19:00;[1000] Grote Club;;5;2;2;1\r\n'
        csv_file += '8;donderdag 17 oktober 2019 om 19:00;[1100] Kleine Club;;0;0;0;0\r\n'
        csv_file += '9;vrijdag 15 november 2019 om 19:00;[1000] Grote Club;;5;2;2;1\r\n'
        csv_file += '\r\nBondsnummer;Sporter;Vereniging;Wedstrijdklasse (individueel);1;2;3;4;5;6;7;8;9\r\n'
        csv_file += '110001;Lid 110001 de Tester;[1000] Grote Club;Barebow Onder 14 Jongens;;;X;;X;;X;;X\r\n'
        csv_file += '110002;Lid 110002 de Tester;[1000] Grote Club;Recurve Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        csv_file += '110003;Lid 110003 de Tester;[1000] Grote Club;Compound Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        csv_file += '110004;Lid 110004 de Tester;[1000] Grote Club;Recurve Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        csv_file += '110005;Lid 110005 de Tester;[1000] Grote Club;Recurve Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        csv_file += '110006;Lid 110006 de Tester;[1100] Kleine Club;Recurve Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        csv_file += '110007;Lid 110007 de Tester;[1100] Kleine Club;Recurve Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        csv_file += '110008;Lid 110008 de Tester;[1100] Kleine Club;Compound Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        csv_file += '110009;Lid 110009 de Tester;[1100] Kleine Club;Recurve Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        csv_file += '110010;Lid 110010 de Tester;[1100] Kleine Club;Recurve Onder 21 klasse onbekend;;;X;;X;;X;;X\r\n'
        self.assertContains(resp, csv_file, msg_prefix="(was: %s)" % resp.content)

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
        url = self.url_behoefte1 % (999999, 101)
        resp = self.client.get(url)
        self.assert403(resp)

    def test_bad_rcl(self):
        comp = Competitie.objects.get(afstand='25')
        functie_rcl = Regiocompetitie.objects.get(competitie=comp,
                                                  regio=self.regio_101).functie

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
