# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from BasisTypen.models import IndivWedstrijdklasse
from Competitie.models import Competitie, maak_competitieklasse_indiv
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

        # fase R: vaststellen en publiceren uitslag
        comp.bk_laatste_wedstrijd = gister
        comp.save()
        return

    comp.alle_rks_afgesloten = False

    if fase >= 'K':
        # RK fases
        comp.alle_regiocompetities_afgesloten = True
        if fase == 'K':
            comp.rk_eerste_wedstrijd = morgen
            comp.save()
            return

        comp.rk_eerste_wedstrijd = gister

        if fase == 'L':
            comp.rk_laatste_wedstrijd = morgen  # vandaag mag ook
            comp.save()
            return

        # fase M: vaststellen en publiceren uitslag
        comp.rk_laatste_wedstrijd = gister
        comp.save()
        return

    comp.alle_regiocompetities_afgesloten = False

    # fase A was totdat de Competitie gemaakt werd

    if fase in ('A1', 'A2'):
        comp.begin_aanmeldingen = morgen
        comp.save()
        return

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

    # fase F: vaststellen en publiceren uitslag
    comp.save()
    return


class TestCompetitieFase(TestCase):

    def test_zet_fase(self):
        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)
        einde_jaar = datetime.date(year=now.year, month=12, day=31)
        gisteren = now - datetime.timedelta(days=1)

        # maak een competitie aan en controleer de fase
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.uiterste_datum_lid = datetime.date(year=2000, month=1, day=1)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = einde_jaar
        comp.eerste_wedstrijd = comp.laatst_mogelijke_wedstrijd = einde_jaar
        comp.rk_eerste_wedstrijd = comp.rk_laatste_wedstrijd = einde_jaar
        comp.bk_eerste_wedstrijd = comp.bk_laatste_wedstrijd = einde_jaar
        comp.save()
        comp.zet_fase()
        self.assertEqual(comp.fase, 'A1')

        comp.begin_aanmeldingen = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'A1')

        # maak de klassen aan en controleer de fase weer
        indiv = IndivWedstrijdklasse.objects.all()[0]
        maak_competitieklasse_indiv(comp, indiv, 0.0)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen
        comp.zet_fase()
        self.assertEqual(comp.fase, 'A2')

        # tussen begin en einde aanmeldingen = B
        comp.begin_aanmeldingen = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'B')

        # na einde aanmeldingen tot einde_teamvorming = C
        comp.einde_aanmeldingen = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'C')

        # na einde teamvorming tot eerste wedstrijd = D
        comp.einde_teamvorming = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'D')

        # na eerste wedstrijd = E
        comp.eerste_wedstrijd = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'E')

        # na laatste wedstrijd = F
        comp.laatst_mogelijke_wedstrijd = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'F')

        comp.alle_regiocompetities_afgesloten = True
        comp.zet_fase()
        self.assertEqual(comp.fase, 'K')

        comp.rk_eerste_wedstrijd = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'L')

        comp.rk_laatste_wedstrijd = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'M')

        comp.alle_rks_afgesloten = True
        comp.zet_fase()
        self.assertEqual(comp.fase, 'P')

        comp.bk_eerste_wedstrijd = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'Q')

        comp.bk_laatste_wedstrijd = gisteren
        comp.zet_fase()
        self.assertEqual(comp.fase, 'R')

        comp.alle_bks_afgesloten = True
        comp.zet_fase()
        self.assertEqual(comp.fase, 'Z')

    def test_zet_competitie_fase(self):
        """ test de helper functie die de competitie fase forceert """
        einde_jaar = datetime.date(year=2000, month=12, day=31)
        comp = Competitie()
        comp.begin_jaar = 2000
        comp.uiterste_datum_lid = datetime.date(year=2000, month=1, day=1)
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = einde_jaar
        comp.eerste_wedstrijd = comp.laatst_mogelijke_wedstrijd = einde_jaar
        comp.rk_eerste_wedstrijd = comp.rk_laatste_wedstrijd = einde_jaar
        comp.bk_eerste_wedstrijd = comp.bk_laatste_wedstrijd = einde_jaar
        comp.save()

        comp.zet_fase()
        self.assertEqual(comp.fase, 'A1')

        zet_competitie_fase(comp, 'A1')
        comp.zet_fase()
        self.assertEqual(comp.fase, 'A1')

        # maak de klassen aan en controleer de fase weer
        indiv = IndivWedstrijdklasse.objects.all()[0]
        maak_competitieklasse_indiv(comp, indiv, 0.0)
        zet_competitie_fase(comp, 'A2')
        comp.zet_fase()
        self.assertEqual(comp.fase, 'A2')

        sequence = 'BCDEFKLMPQRZRQPMLKFEDCBKREBRLQC'
        for fase in sequence:
            zet_competitie_fase(comp, fase)
            comp.zet_fase()
            self.assertEqual(comp.fase, fase)
        # for

# end of file
