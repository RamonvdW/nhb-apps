# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbLid


class SchutterVoorkeuren(models.Model):
    """ OBSOLETE - gebruik SporterVoorkeuren """
    nhblid = models.ForeignKey(NhbLid, on_delete=models.CASCADE, null=True)
    voorkeur_eigen_blazoen = models.BooleanField(default=False)
    voorkeur_meedoen_competitie = models.BooleanField(default=True)
    opmerking_para_sporter = models.CharField(max_length=256, default='')
    voorkeur_discipline_25m1pijl = models.BooleanField(default=True)
    voorkeur_discipline_outdoor = models.BooleanField(default=True)
    voorkeur_discipline_indoor = models.BooleanField(default=True)
    voorkeur_discipline_clout = models.BooleanField(default=True)
    voorkeur_discipline_veld = models.BooleanField(default=True)
    voorkeur_discipline_run = models.BooleanField(default=True)
    voorkeur_discipline_3d = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = verbose_name = "Schutter voorkeuren"


class SchutterBoog(models.Model):
    """ OBSOLETE - gebruik SporterBoog """
    nhblid = models.ForeignKey(NhbLid, on_delete=models.CASCADE, null=True)
    boogtype = models.ForeignKey(BoogType, on_delete=models.CASCADE)
    heeft_interesse = models.BooleanField(default=True)
    voor_wedstrijd = models.BooleanField(default=False)

    class Meta:
        verbose_name = "SchutterBoog"
        verbose_name_plural = "SchuttersBoog"


# end of file
