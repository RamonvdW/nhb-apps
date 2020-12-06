# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0013_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='aantal_scores',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='alt_aantal_scores',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]

# end of file
