# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import GESLACHT_MV, GESLACHT_MAN
from .sporter import Sporter


class SporterVoorkeuren(models.Model):
    """ Globale voorkeuren voor een sporter, onafhankelijk van zijn boog """

    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # (opt-in) voorkeur voor eigen blazoen: Dutch Target (Recurve) of 60cm 4spot (Compound)
    voorkeur_eigen_blazoen = models.BooleanField(default=False)

    # (opt-out) wel/niet aanbieden om mee te doen met de competitie
    voorkeur_meedoen_competitie = models.BooleanField(default=True)

    # open notitie aan de wedstrijdleiding
    opmerking_para_sporter = models.CharField(max_length=256, default='', blank=True)

    # notificatie aan de wedstrijdleiding: sporter gebruikt voorwerpen die op de schietlijn blijven staan
    # (hierdoor kunnen er minder sporters op zijn baan)
    para_voorwerpen = models.BooleanField(default=False)

    # (opt-out) voorkeur voor wedstrijden van specifieke disciplines
    voorkeur_discipline_25m1pijl = models.BooleanField(default=True)
    voorkeur_discipline_outdoor = models.BooleanField(default=True)
    voorkeur_discipline_indoor = models.BooleanField(default=True)      # Indoor = 18m/25m 3pijl
    voorkeur_discipline_clout = models.BooleanField(default=True)
    voorkeur_discipline_veld = models.BooleanField(default=True)
    voorkeur_discipline_run = models.BooleanField(default=True)
    voorkeur_discipline_3d = models.BooleanField(default=True)

    # het geslacht voor wedstrijden
    # alleen te kiezen voor sporters met geslacht='X'
    # automatisch gelijk gesteld aan het geslacht voor sporters met geslacht='M' of 'V'
    wedstrijd_geslacht_gekozen = models.BooleanField(default=True)
    wedstrijd_geslacht = models.CharField(max_length=1, choices=GESLACHT_MV, default=GESLACHT_MAN)

    # opt-in voor het delen van contactgegevens met het korps SR
    scheids_opt_in_korps_tel_nr = models.BooleanField(default=False)
    scheids_opt_in_korps_email = models.BooleanField(default=False)

    # opt-in voor het delen van contactgegevens met de organiserende vereniging
    # van een wedstrijd waar de SR voor geselecteerd is
    scheids_opt_in_ver_tel_nr = models.BooleanField(default=False)
    scheids_opt_in_ver_email = models.BooleanField(default=False)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name_plural = verbose_name = "Sporter voorkeuren"

    def __str__(self):
        return "%s" % self.sporter.lid_nr

    objects = models.Manager()      # for the editor only


# end of file
