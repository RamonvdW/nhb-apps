# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from BasisTypen.models import IndivWedstrijdklasse
from Competitie.models import (Competitie, DeelCompetitie, CompetitieKlasse,
                               LAAG_REGIO, LAAG_RK, LAAG_BK)
import datetime


def zet_competitie_fase(comp, fase):
    """ deze helper weet hoe de competitie datums gemanipuleerd moeten worden
        zodat models.Competitie.zet_fase() de gevraagde fase terug zal geven
    """

    if fase == 'Z':
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
            comp.datum_klassegrenzen_rk_bk_teams = False
            return

        comp.klassegrenzen_vastgesteld_rk_bk = True

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
        comp.klassegrenzen_vastgesteld = False
        comp.save()
        return

    if comp.competitieklasse_set.count() == 0:      # pragma: no cover
        raise NotImplementedError("Kan niet naar fase %s zonder competitie klassen!" % fase)

    comp.klassegrenzen_vastgesteld = True
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

    # fase F of G: vaststellen uitslag in elke regio + afsluiten regiocompetitie
    comp.save()
    return


class TestCompetitieFase(TestCase):

    """ tests voor de Competitie applicatie, hanteren van de competitie fases """

    def test_zet_fase(self):
        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)
        einde_jaar = datetime.date(year=now.year, month=12, day=31)
        if now == einde_jaar:                           # pragma: no cover
            einde_jaar += datetime.timedelta(days=1)    # needed once a year..
        gisteren = now - datetime.timedelta(days=1)

        # maak een competitie aan en controleer de fase
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.uiterste_datum_lid = datetime.date(year=2000, month=1, day=1)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = einde_jaar
        comp.eerste_wedstrijd = comp.laatst_mogelijke_wedstrijd = einde_jaar
        comp.datum_klassegrenzen_rk_bk_teams = einde_jaar
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
        indiv = IndivWedstrijdklasse.objects.all()[0]
        CompetitieKlasse(competitie=comp, indiv=indiv, min_ag=0.0).save()
        comp.begin_aanmeldingen = comp.einde_aanmeldingen
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        comp.klassegrenzen_vastgesteld = True
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

        comp.klassegrenzen_vastgesteld_rk_bk = True
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
        self.assertEqual(comp.fase, 'Z')

    def test_zet_competitie_fase(self):
        """ test de helper functie die de competitie fase forceert """
        einde_jaar = datetime.date(year=2000, month=12, day=31)
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.uiterste_datum_lid = datetime.date(year=2000, month=1, day=1)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = einde_jaar
        comp.eerste_wedstrijd = comp.laatst_mogelijke_wedstrijd = einde_jaar
        comp.datum_klassegrenzen_rk_bk_teams = einde_jaar
        comp.rk_eerste_wedstrijd = comp.rk_laatste_wedstrijd = einde_jaar
        comp.bk_eerste_wedstrijd = comp.bk_laatste_wedstrijd = einde_jaar
        comp.save()

        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        zet_competitie_fase(comp, 'A')
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        # maak de klassen aan en controleer de fase weer
        indiv = IndivWedstrijdklasse.objects.all()[0]
        CompetitieKlasse(competitie=comp, indiv=indiv, min_ag=0.0).save()
        zet_competitie_fase(comp, 'A')
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        comp.klassegrenzen_vastgesteld = True
        zet_competitie_fase(comp, 'A')
        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'A')

        sequence = 'BCDEGKLNPQSQPNLKGEDCBKSEBZLQC'  # let op! F en R kunnen niet
        for fase in sequence:
            zet_competitie_fase(comp, fase)
            comp.bepaal_fase()
            self.assertEqual(comp.fase, fase)
        # for

# end of file
