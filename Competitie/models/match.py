# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Locatie.models import WedstrijdLocatie
from Score.models import Uitslag
from Vereniging.models import Vereniging


class CompetitieMatch(models.Model):
    """ CompetitieMatch is de kleinste planbare eenheid in de bondscompetitie """

    # hoort bij welke competitie?
    # (ook nuttig voor filteren toepasselijke indiv_klassen / team_klassen)
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # beschrijving
    beschrijving = models.CharField(max_length=100, blank=True)

    # organiserende vereniging
    vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT,
                                   blank=True, null=True)   # mag later ingevuld worden

    # waar
    locatie = models.ForeignKey(WedstrijdLocatie, on_delete=models.PROTECT,
                                blank=True, null=True)      # mag later ingevuld worden

    # datum en tijdstippen
    datum_wanneer = models.DateField()
    tijd_begin_wedstrijd = models.TimeField()

    # competitie klassen individueel en teams
    indiv_klassen = models.ManyToManyField(CompetitieIndivKlasse,
                                           blank=True)  # mag leeg zijn / gemaakt worden

    team_klassen = models.ManyToManyField(CompetitieTeamKlasse,
                                          blank=True)  # mag leeg zijn / gemaakt worden

    # uitslag / scores
    uitslag = models.ForeignKey(Uitslag, on_delete=models.PROTECT,
                                blank=True, null=True)

    # benodigde scheidsrechters
    aantal_scheids = models.IntegerField(default=0)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        extra = ""
        if self.vereniging:
            extra = " bij %s" % self.vereniging
        return "(%s) %s %s%s" % (self.pk, self.datum_wanneer, self.tijd_begin_wedstrijd, extra)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Competitie match"
        verbose_name_plural = "Competitie matches"


# end of file
