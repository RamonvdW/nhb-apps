# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Competitie.definities import (INSCHRIJF_METHODES, INSCHRIJF_METHODE_2,
                                   TEAM_PUNTEN, TEAM_PUNTEN_MODEL_TWEE)
from Competitie.models.competitie import Competitie
from Functie.models import Functie
from Geo.models import Regio


class RegioComp(models.Model):

    """ Regio fase van de bondscompetitie in een regio (16x) """

    # hoort bij welke competitie?
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # regio
    regio = models.ForeignKey(Regio, on_delete=models.PROTECT)

    # welke beheerder hoort hier bij?
    functie = models.ForeignKey(Functie, on_delete=models.PROTECT)

    # is de beheerder klaar?
    is_afgesloten = models.BooleanField(default=False)

    # de RCL bepaalt in welke ronde van de competitie we zijn
    #    0 = initieel
    # 1..7 = wedstrijd ronde
    #    8 = afgesloten
    huidige_team_ronde = models.PositiveSmallIntegerField(default=0)

    # specifieke instellingen voor deze regio
    inschrijf_methode = models.CharField(max_length=1,
                                         default=INSCHRIJF_METHODE_2,
                                         choices=INSCHRIJF_METHODES)

    # methode 3: toegestane dagdelen
    # komma-gescheiden lijstje met DAGDEEL: GE,AV
    # LET OP: leeg = alles toegestaan!
    toegestane_dagdelen = models.CharField(max_length=40, default='', blank=True)

    # keuzes van de RCL voor de regiocompetitie teams

    # doet deze regiocompetitie aan team competitie?
    regio_organiseert_teamcompetitie = models.BooleanField(default=True)

    # vaste teams? zo niet, dan voortschrijdend gemiddelde (VSG)
    regio_heeft_vaste_teams = models.BooleanField(default=True)

    # tot welke datum mogen teams aangemeld aangemaakt worden (verschilt per regio)
    begin_fase_D = models.DateField(default='2001-01-01')

    # punten model
    regio_team_punten_model = models.CharField(max_length=2,
                                               default=TEAM_PUNTEN_MODEL_TWEE,
                                               choices=TEAM_PUNTEN)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = "%s - %s" % (self.competitie, self.regio)
        if self.is_afgesloten:
            msg = '(afgesloten) ' + msg
        return msg

    class Meta:
        verbose_name = 'Regio competitie'

    objects = models.Manager()      # for the editor only


# end of file
