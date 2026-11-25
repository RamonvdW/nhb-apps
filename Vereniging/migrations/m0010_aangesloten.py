# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0009_externe_scores_2'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='vereniging',
            name='aangesloten_vanaf',
            field=models.DateField(blank=True, default='1990-01-01', null=True),
        ),
        migrations.AddField(
            model_name='vereniging',
            name='aangesloten_tot',
            field=models.DateField(blank=True, default='3333-12-31', null=True),
        ),
        migrations.AddField(
            model_name='vereniging',
            name='is_actief',
            field=models.BooleanField(default=True),
        ),
    ]

# end of file
