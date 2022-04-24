# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0064_order'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapschutterboog',
            name='result_counts',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='kampioenschapschutterboog',
            name='result_rank',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='kampioenschapschutterboog',
            name='result_score_1',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='kampioenschapschutterboog',
            name='result_score_2',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]

# end of file
