# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0015_squashed'),
    ]

    # migration functions
    operations = [
        migrations.RenameModel(
            old_name='HistKampIndiv',
            new_name='HistKampIndivRK',
        ),
        migrations.AlterModelOptions(
            name='histkampteam',
            options={'verbose_name': 'Hist RK/BK teams', 'verbose_name_plural': 'Hist RK/BK teams'},
        ),
        migrations.AddField(
            model_name='histkampteam',
            name='team_score_counts',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]

# end of file
