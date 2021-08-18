# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0046_voorkeur_avond'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='deelcompetitie',
            name='huidige_team_ronde',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='regiocompetitierondeteam',
            name='logboek',
            field=models.TextField(blank=True, max_length=1024),
        ),
    ]

# end of file
