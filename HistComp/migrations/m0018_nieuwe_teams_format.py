# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0017_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='histcompseizoen',
            name='head_to_head_teams_format',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='histkampteam',
            name='team_score_is_blanco',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
