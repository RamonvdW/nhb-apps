# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse
from NhbStructuur.models import NhbVereniging

# TODO: uitbreiden met meer mogelijkheden zoals buitenbaan, veld, 3D, etc.
BAAN_TYPE = (('X', 'Onbekend'),
             ('O', 'Volledig overdekte binnenbaan'),
             ('H', 'Binnen-buiten schieten'))

BAANTYPE2STR = {
    'X': 'Onbekend',
    'O': 'Volledig overdekte binnenbaan',
    'H': 'Binnen-buiten schieten',
}


class WedstrijdLocatie(models.Model):
    """ Een locatie waarop een wedstrijd gehouden kan worden
        Niet noodzakelijk het doel van een vereniging.
    """

    # zichtbaar maakt het mogelijk een baan uit het systeem te halen
    # zonder deze helemaal te verwijderen
    zichtbaar = models.BooleanField(default=True)

    # verenigingen die deze locatie gebruiken (kan gedeeld doel zijn)
    verenigingen = models.ManyToManyField(NhbVereniging)

    baan_type = models.CharField(max_length=1, choices=BAAN_TYPE, default='X')

    # informatie over de beschikbare banen voor de indoor wedstrijden
    banen_18m = models.PositiveSmallIntegerField(default=0)
    banen_25m = models.PositiveSmallIntegerField(default=0)
    max_dt_per_baan = models.PositiveSmallIntegerField(default=4)

    # adresgegevens van het doel/veld
    adres = models.TextField(max_length=256, blank=True)

    # handmatig ingevoerd of uit de CRM
    adres_uit_crm = models.BooleanField(default=False)

    # vrije notitiegegevens voor zaken als "verbouwing tot", etc.
    notities = models.TextField(max_length=1024, blank=True)

    def __str__(self):
        if not self.zichtbaar:
            msg = "(hidden) "
        else:
            msg = ""
        msg += self.adres.replace('\n', ', ')
        msg += " (%s verenigingen)" % self.verenigingen.count()
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijdlocatie"
        verbose_name_plural = "Wedstrijdlocaties"


class Wedstrijd(models.Model):
    """ Wedstrijd is de kleinste planbare eenheid """

    # beschrijving
    beschrijving = models.CharField(max_length=100, blank=True)

    # plan status
    preliminair = models.BooleanField(default=True)

    # organiserende vereniging
    vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                   blank=True, null=True)   # mag later ingevuld worden

    # waar
    locatie = models.ForeignKey(WedstrijdLocatie, on_delete=models.PROTECT,
                                blank=True, null=True)      # mag later ingevuld worden

    # datum en tijdstippen
    datum_wanneer = models.DateField()
    tijd_begin_aanmelden = models.TimeField()
    tijd_begin_wedstrijd = models.TimeField()
    tijd_einde_wedstrijd = models.TimeField()

    # wedstrijdklassen individueel en teams
    indiv_klassen = models.ManyToManyField(IndivWedstrijdklasse)
    team_klassen = models.ManyToManyField(TeamWedstrijdklasse)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijd"
        verbose_name_plural = "Wedstrijden"


class WedstrijdenPlan(models.Model):
    """ Planning voor een serie wedstrijden, zoals de competitierondes """

    # lijst van wedstrijden
    wedstrijden = models.ManyToManyField(Wedstrijd)

    # de hiaat vlag geeft snel weer of er een probleem in de planning zit
    bevat_hiaat = models.BooleanField(default=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijdenplan"
        verbose_name_plural = "Wedstrijdenplannen"

# end of file
