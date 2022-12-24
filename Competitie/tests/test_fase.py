# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from BasisTypen.models import TemplateCompetitieIndivKlasse, TeamType
from Competitie.models import (Competitie, DeelCompetitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               LAAG_REGIO, LAAG_RK, LAAG_BK)
from Functie.models import Rollen
import datetime


def zet_competitie_fase(comp, fase):
    """ deze helper weet hoe de competitie datums gemanipuleerd moeten worden
        zodat models.Competitie.bepaal_fase() de gevraagde fase terug zal geven
    """

    if fase == 'Z':
        comp.is_afgesloten = True
        comp.save()
        return

    comp.is_afgesloten = False

    if fase == 'S':
        comp.alle_bks_afgesloten = True
        comp.save()
        return

    comp.alle_bks_afgesloten = False

    now = timezone.now()
    vandaag = datetime.date(year=now.year, month=now.month, day=now.day)
    gister = vandaag - datetime.timedelta(days=1)
    morgen = vandaag + datetime.timedelta(days=1)

    if fase >= 'P':
        # BK fases
        comp.alle_rks_afgesloten = True
        if fase == 'P':
            comp.bk_eerste_wedstrijd = morgen
            comp.save()
            return

        comp.bk_eerste_wedstrijd = gister

        if fase == 'Q':
            comp.bk_laatste_wedstrijd = morgen  # vandaag mag ook
            comp.save()
            return

        # fase R of S: vaststellen uitslagen + afsluiten BK
        comp.bk_laatste_wedstrijd = gister
        comp.save()
        return

    comp.alle_rks_afgesloten = False

    if fase >= 'J':
        # RK fases
        comp.alle_regiocompetities_afgesloten = True

        if fase == 'J':
            comp.klassengrenzen_vastgesteld_rk_bk = False
            comp.datum_klassengrenzen_rk_bk_teams = morgen
            comp.save()
            return

        comp.klassengrenzen_vastgesteld_rk_bk = True

        if fase == 'K':
            comp.rk_eerste_wedstrijd = morgen + datetime.timedelta(days=14)
            comp.save()
            return

        comp.rk_eerste_wedstrijd = gister

        if fase == 'L':
            comp.rk_laatste_wedstrijd = morgen  # vandaag mag ook
            comp.save()
            return

        # fase M of N: vaststellen uitslag in elk rayon + afsluiten RK
        comp.rk_laatste_wedstrijd = gister
        comp.save()
        return

    comp.alle_regiocompetities_afgesloten = False

    # fase A begon toen de competitie werd aangemaakt

    if fase == 'A':
        comp.begin_aanmeldingen = morgen
        comp.klassengrenzen_vastgesteld = False
        comp.save()
        return

    if comp.competitieindivklasse_set.count() == 0:      # pragma: no cover
        raise NotImplementedError("Kan niet naar fase %s zonder competitie indiv klassen!" % fase)

    if comp.competitieteamklasse_set.count() == 0:      # pragma: no cover
        raise NotImplementedError("Kan niet naar fase %s zonder competitie team klassen!" % fase)

    comp.klassengrenzen_vastgesteld = True
    comp.begin_aanmeldingen = gister

    if fase == 'B':
        comp.einde_aanmeldingen = morgen
        comp.save()
        return

    comp.einde_aanmeldingen = gister

    if fase == 'C':
        comp.einde_teamvorming = morgen     # vandaag mag ook
        comp.save()
        return

    comp.einde_teamvorming = gister

    if fase == 'D':
        comp.eerste_wedstrijd = morgen
        comp.save()
        return

    comp.eerste_wedstrijd = gister

    if fase == 'E':
        comp.laatst_mogelijke_wedstrijd = morgen
        comp.save()
        return

    comp.laatst_mogelijke_wedstrijd = gister

    if fase == 'G':
        # alle regios afsluiten
        for deelcomp in comp.deelcompetitie_set.filter(is_afgesloten=False, laag=LAAG_REGIO):
            deelcomp.is_afgesloten = True
            deelcomp.save(update_fields=['is_afgesloten'])
        comp.save()
        return

    # fase F: vaststellen uitslag in elke regio + afsluiten regiocompetitie
    comp.save()
    return


class TestCompetitieFase(TestCase):

    """ tests voor de Competitie applicatie, hanteren van de competitie fases """

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

        deelcomp_regio = DeelCompetitie(competitie=comp,
                                        is_afgesloten=False,
                                        laag=LAAG_REGIO)
        deelcomp_regio.save()

        deelcomp_rk = DeelCompetitie(competitie=comp,
                                     is_afgesloten=False,
                                     laag=LAAG_RK)
        deelcomp_rk.save()

        deelcomp_bk = DeelCompetitie(competitie=comp,
                                     is_afgesloten=False,
                                     laag=LAAG_BK)
        deelcomp_bk.save()

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
        deelcomp_rk.is_afgesloten = True
        deelcomp_rk.save()
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
        deelcomp_bk.is_afgesloten = True
        deelcomp_bk.save()
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


# end of file
