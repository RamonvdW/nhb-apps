# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0120_nieuwe_teams_format'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapteam',
            name='result_shootoff_str',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]

# end of file
