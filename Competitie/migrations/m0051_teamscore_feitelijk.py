# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0009_squashed'),
        ('Competitie', 'm0050_rondeteam_feitelijk'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitierondeteam',
            name='scorehist_feitelijk',
            field=models.ManyToManyField(blank=True, related_name='teamronde_feitelijk', to='Score.ScoreHist'),
        ),
        migrations.AddField(
            model_name='regiocompetitierondeteam',
            name='scores_feitelijk',
            field=models.ManyToManyField(blank=True, related_name='teamronde_feitelijk', to='Score.Score'),
        ),
    ]

# end of file
