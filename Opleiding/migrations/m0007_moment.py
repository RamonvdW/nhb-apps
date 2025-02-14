# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleiding', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='opleidingmoment',
            name='aantal_dagen',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='opleidingmoment',
            name='opleider_naam',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
    ]

# end of file
