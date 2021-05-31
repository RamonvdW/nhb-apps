# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_deelnemer_dagdelen(apps, _):
    """ pas de dagdeel voorkeuren aan voor de ingeschreven deelnemers """

    deelnemer_klas = apps.get_model('Competitie', 'RegioCompetitieSchutterBoog')

    # ZA --> ZAT
    for deelnemer in deelnemer_klas.objects.filter(inschrijf_voorkeur_dagdeel='ZA'):        # pragma: no cover
        deelnemer.inschrijf_voorkeur_dagdeel = 'ZAT'
        deelnemer.save()
    # for

    # ZO --> ZON
    for deelnemer in deelnemer_klas.objects.filter(inschrijf_voorkeur_dagdeel='ZO'):        # pragma: no cover
        deelnemer.inschrijf_voorkeur_dagdeel = 'ZON'
        deelnemer.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0040_dagdelen'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(migreer_deelnemer_dagdelen)
    ]

# end of file
