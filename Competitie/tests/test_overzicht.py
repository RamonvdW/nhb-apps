# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from BasisTypen.models import TemplateCompetitieIndivKlasse, TeamType
from Competitie.models import (Competitie, DeelCompetitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               DeelKampioenschap, DEEL_RK, DEEL_BK)
from Competitie.tests.test_helpers import zet_competitie_fase, maak_competities_en_zet_fase_b
from Functie.models import Rollen, Functie
from NhbStructuur.models import NhbRegio
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestCompetitieOverzicht(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, pagina Overzicht """

    url_overzicht = '/bondscompetities/%s/'

    @staticmethod
    def _maak_twee_klassen(comp):
        indiv = TemplateCompetitieIndivKlasse.objects.all()[0]
        CompetitieIndivKlasse(competitie=comp, volgorde=1, boogtype=indiv.boogtype, min_ag=0.0).save()

        teamtype = TeamType.objects.all()[0]
        CompetitieTeamKlasse(competitie=comp, volgorde=1, min_ag=0.0, team_type=teamtype).save()

    def test_zet_fase(self):
        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)
        einde_jaar = datetime.date(year=now.year, month=12, day=31)
        # einde_jaar is goed, behalve in the laatste 2 weken
        if now > einde_jaar - datetime.timedelta(days=15):       # pragma: no cover
            einde_jaar += datetime.timedelta(days=15)
        gisteren = now - datetime.timedelta(days=1)

        # maak een competitie aan en controleer de fase
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.uiterste_datum_lid = datetime.date(year=2000, month=1, day=1)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = einde_jaar
        comp.eerste_wedstrijd = comp.laatst_mogelijke_wedstrijd = einde_jaar
        comp.datum_klassengrenzen_rk_bk_teams = einde_jaar
        comp.rk_eerste_wedstrijd = comp.rk_laatste_wedstrijd = einde_jaar
        comp.bk_eerste_wedstrijd = comp.bk_laatste_wedstrijd = einde_jaar
        comp.save()

        dummy_functie = Functie.objects.get(rol='MWZ')
        regio_116 = NhbRegio.objects.get(regio_nr=116)

        deelcomp_regio = DeelCompetitie(competitie=comp,
                                        is_afgesloten=False,
                                        nhb_regio=regio_116,
                                        functie=dummy_functie)
        deelcomp_regio.save()

        deelkamp_rk = DeelKampioenschap(competitie=comp,
                                        is_afgesloten=False,
                                        deel=DEEL_RK,
                                        functie=dummy_functie)
        deelkamp_rk.save()

        deelkamp_bk = DeelKampioenschap(competitie=comp,
                                        is_afgesloten=False,
                                        deel=DEEL_BK,
                                        functie=dummy_functie)
        deelkamp_bk.save()

        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        comp.begin_aanmeldingen = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        # maak de klassen aan
        self._maak_twee_klassen(comp)

        comp.begin_aanmeldingen = comp.einde_aanmeldingen
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        comp.klassengrenzen_vastgesteld = True
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        # tussen begin en einde aanmeldingen = B
        comp.begin_aanmeldingen = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'B')

        # na einde aanmeldingen tot einde_teamvorming = C
        comp.einde_aanmeldingen = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'C')

        # na einde teamvorming tot eerste wedstrijd = D
        comp.einde_teamvorming = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'D')

        # na eerste wedstrijd = E
        comp.eerste_wedstrijd = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'E')

        # na laatste wedstrijd = F
        comp.laatst_mogelijke_wedstrijd = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'F')

        # na afsluiten regio deelcomp = G
        deelcomp_regio.is_afgesloten = True
        deelcomp_regio.save()
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'G')

        comp.alle_regiocompetities_afgesloten = True
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'J')

        comp.klassengrenzen_vastgesteld_rk_bk = True
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'K')

        comp.rk_eerste_wedstrijd = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'L')

        comp.rk_laatste_wedstrijd = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'M')

        # na afsluiten RK = N
        deelkamp_rk.is_afgesloten = True
        deelkamp_rk.save()
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'N')

        comp.alle_rks_afgesloten = True
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'P')

        comp.bk_eerste_wedstrijd = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'Q')

        comp.bk_laatste_wedstrijd = gisteren
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'R')

        # na afsluiten BK = S
        deelkamp_bk.is_afgesloten = True
        deelkamp_bk.save()
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'S')

        comp.alle_bks_afgesloten = True
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'S')

        comp.is_afgesloten = True
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'Z')

    def test_zet_competitie_fase(self):
        # test de helper functie die de competitie fase forceert
        einde_jaar = datetime.date(year=2000, month=12, day=31)
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.uiterste_datum_lid = datetime.date(year=2000, month=1, day=1)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = einde_jaar
        comp.eerste_wedstrijd = comp.laatst_mogelijke_wedstrijd = einde_jaar
        comp.datum_klassengrenzen_rk_bk_teams = einde_jaar
        comp.rk_eerste_wedstrijd = comp.rk_laatste_wedstrijd = einde_jaar
        comp.bk_eerste_wedstrijd = comp.bk_laatste_wedstrijd = einde_jaar
        comp.save()

        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        zet_competitie_fase(comp, 'A')
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        # maak de klassen aan en controleer de fase weer
        self._maak_twee_klassen(comp)
        zet_competitie_fase(comp, 'A')
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        comp.klassengrenzen_vastgesteld = True
        zet_competitie_fase(comp, 'A')
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        sequence = 'BCDEGJKLNPQSQPNLKJGEDCBKSEBZLQC'  # let op! F en R kunnen niet
        for fase in sequence:
            zet_competitie_fase(comp, fase)
            comp.bepaal_fase()
            self.assertEqual(comp.fase, fase)
        # for

    def test_openbaar(self):
        einde_jaar = datetime.date(year=2000, month=12, day=31)
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.uiterste_datum_lid = datetime.date(year=2000, month=1, day=1)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = einde_jaar
        comp.eerste_wedstrijd = comp.laatst_mogelijke_wedstrijd = einde_jaar
        comp.datum_klassengrenzen_rk_bk_teams = einde_jaar
        comp.rk_eerste_wedstrijd = comp.rk_laatste_wedstrijd = einde_jaar
        comp.bk_eerste_wedstrijd = comp.bk_laatste_wedstrijd = einde_jaar
        comp.save()

        zet_competitie_fase(comp, 'A')

        # altijd openbaar voor BB en BKO
        comp.bepaal_openbaar(Rollen.ROL_BB)
        self.assertTrue(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_BKO)
        self.assertTrue(comp.is_openbaar)

        # altijd openbaar voor RKO/RCL/HWL
        comp.bepaal_openbaar(Rollen.ROL_RKO)
        self.assertTrue(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_RCL)
        self.assertTrue(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_HWL)
        self.assertTrue(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_WL)
        self.assertFalse(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_SEC)
        self.assertFalse(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_MO)
        self.assertFalse(comp.is_openbaar)

        comp.bepaal_openbaar(Rollen.ROL_SPORTER)
        self.assertFalse(comp.is_openbaar)

        # vanaf fase B altijd openbaar
        comp.fase = 'B'

        comp.bepaal_openbaar(Rollen.ROL_SPORTER)
        self.assertTrue(comp.is_openbaar)

    def test_top(self):
        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)
        way_before = datetime.date(year=2018, month=1, day=1)   # must be before timezone.now()

        comp_18, comp_25 = maak_competities_en_zet_fase_b(startjaar=2020)

        comp = comp_25

        # fase A
        comp.begin_aanmeldingen = now + datetime.timedelta(days=1)      # morgen
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase < 'B', msg="comp.fase=%s (expected: below B)" % comp.fase)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # zet competitie fase B zodat we in mogen schrijven
        zet_competitie_fase(comp, 'B')

        # uitslagen met competitie in prep fase (B+)
        comp.begin_aanmeldingen = way_before   # fase B
        comp.einde_aanmeldingen = way_before   # fase C
        comp.save()
        comp.bepaal_fase()
        # self.assertTrue(comp.fase >= 'B')
        self.assertTrue(comp.fase >= 'B', msg="comp.fase=%s (expected: not below B)" % comp.fase)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        # uitslagen met competitie in scorende fase (E+)
        comp.einde_teamvorming = way_before    # fase D
        comp.eerste_wedstrijd = way_before     # fase E
        comp.save()
        comp.bepaal_fase()
        self.assertTrue(comp.fase >= 'E')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.client.logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht % comp_18.pk)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/overzicht.dtl', 'plein/site_layout.dtl'))


# end of file
