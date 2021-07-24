# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def init_max_sporters(apps, _):
    """ Zet de nieuwe max_sporters_18m/25m velden """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    locatie_klas = apps.get_model('Wedstrijden', 'WedstrijdLocatie')

    for locatie in locatie_klas.objects.all():                  # pragma: no cover
        locatie.max_sporters_18m = 4 * locatie.banen_18m
        locatie.max_sporters_25m = 4 * locatie.banen_25m
        locatie.save(update_fields=['max_sporters_18m', 'max_sporters_25m'])
    # for


class Migration(migrations.Migration):

    dependencies = [
        ('Wedstrijden', 'm0018_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='max_sporters_18m',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='max_sporters_25m',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.RunPython(init_max_sporters)
    ]

# end of file
