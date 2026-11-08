# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0008_externe_scores'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='externescores',
            name='type',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Onbekend'), (1, 'Centaur'), (2, 'Arrowcast')], default=0),
        ),
        migrations.AddField(
            model_name='externescores',
            name='token',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]

# end of file
