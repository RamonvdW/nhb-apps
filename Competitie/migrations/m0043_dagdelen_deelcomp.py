# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_dagdelen_deelcomp(apps, _):
    """ pas de dagdeel voorkeuren aan voor de ingeschreven deelnemers """

    deelcomp_klas = apps.get_model('Competitie', 'DeelCompetitie')

    for deelcomp in deelcomp_klas.objects.all():
        if deelcomp.toegestane_dagdelen:
            nieuw = list()
            for part in deelcomp.toegestane_dagdelen.split(','):
                if part == 'ZA':
                    part = 'ZAT'
                elif part == 'ZO':
                    part = 'ZON'
                nieuw.append(part)
            # for
            deelcomp.toegestane_dagdelen = ",".join(nieuw)
            deelcomp.save(update_fields=['toegestane_dagdelen'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0042_einde_teams_aanmaken'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(migreer_dagdelen_deelcomp)
    ]

# end of file
