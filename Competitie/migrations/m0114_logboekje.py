# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0113_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitiesporterboog',
            name='logboekje',
            field=models.TextField(blank=True, default=''),
        ),
    ]

# end of file
