# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='buiten_banen',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='wedstrijdlocatie',
            name='buiten_max_afstand',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='wedstrijdlocatie',
            name='baan_type',
            field=models.CharField(choices=[('X', 'Onbekend'), ('O', 'Volledig overdekte binnenbaan'), ('H', 'Binnen-buiten schieten'), ('B', 'Buitenbaan')], default='X', max_length=1),
        ),
    ]

# end of file
