# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import (ORGANISATIES, ORGANISATIE_WA,
                                   GESLACHT_ALLE,
                                   WEDSTRIJDGESLACHT_MVA,
                                   MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                                   BLAZOEN_CHOICES, BLAZOEN_40CM, BLAZOEN_60CM)


class Leeftijdsklasse(models.Model):
    """ definitie van een leeftijdsklasse """

    # WA, IFAA of nationaal
    organisatie = models.CharField(max_length=1, choices=ORGANISATIES, default=ORGANISATIE_WA)

    # SH = Senioren heren, etc.
    afkorting = models.CharField(max_length=5)

    # complete beschrijving: 'Onder 18, meisjes'
    beschrijving = models.CharField(max_length=80)      # CH Cadetten, mannen

    # korte beschrijving: 'Onder 18', etc.
    klasse_kort = models.CharField(max_length=30)

    # man, vrouw of genderneutraal
    wedstrijd_geslacht = models.CharField(max_length=1, choices=WEDSTRIJDGESLACHT_MVA)

    # leeftijdsgrenzen voor de klassen: of ondergrens, of bovengrens
    #   de jeugdklassen hebben een leeftijd bovengrens
    #   de masters en veteranen klassen hebben een leeftijd ondergrens
    #   de senioren klasse heeft helemaal geen grens
    min_wedstrijdleeftijd = models.IntegerField()
    max_wedstrijdleeftijd = models.IntegerField()

    # presentatie volgorde: aspirant als laagste, veteraan als hoogste
    #  gender sub-volgorde: neutraal, man, vrouw
    volgorde = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s %s" % (self.afkorting,
                          self.beschrijving)

    def is_aspirant_klasse(self):
        # <senior  heeft min = 0 en max <21
        # senior   heeft min = 0 en max = 0
        # >senior  heeft min >49 en max = 0     (komt niet voor in de competitie)
        return 0 < self.max_wedstrijdleeftijd <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT

    def leeftijd_is_compatible(self, wedstrijdleeftijd):
        """ voldoet de wedstrijdleeftijd aan de eisen van deze wedstrijdklasse? """

        if wedstrijdleeftijd < self.min_wedstrijdleeftijd:
            # voldoet niet aan ondergrens
            return False

        if self.max_wedstrijdleeftijd and wedstrijdleeftijd > self.max_wedstrijdleeftijd:
            # voldoet niet aan de bovengrens
            return False

        # voldoet aan de eisen
        return True

    def geslacht_is_compatible(self, wedstrijd_geslacht):
        """ past het wedstrijdgeslacht van de sporter bij deze leeftijdsklasse?

            leeftijdsklasse 'A' (alle) past bij alle wedstrijdgeslachten
            anders moet het een 'M'/'V' match zijn
        """
        return (self.wedstrijd_geslacht == GESLACHT_ALLE) or (wedstrijd_geslacht == self.wedstrijd_geslacht)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Leeftijdsklasse"
        verbose_name_plural = "Leeftijdsklassen"

        ordering = ['volgorde']

        # FUTURE: index voor organisatie, in combinatie met afkorting/volgorde??

    objects = models.Manager()      # for the editor only


# end of file
