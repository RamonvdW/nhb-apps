# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0058_allow_blank'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='wedstrijd',
            name='titel',
            field=models.CharField(default='', max_length=75),
        ),
    ]

# end of file
