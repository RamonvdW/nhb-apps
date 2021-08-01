# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0048_rename_mutatie'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='gemiddelde_begin_team_ronde',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=5),
        ),
    ]

# end of file
