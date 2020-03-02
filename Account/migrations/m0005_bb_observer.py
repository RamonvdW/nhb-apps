# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0004_2fa'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='account',
            name='is_BKO',
        ),
        migrations.AddField(
            model_name='account',
            name='is_BB',
            field=models.BooleanField(default=False, help_text='Manager Competitiezaken'),
        ),
        migrations.AddField(
            model_name='account',
            name='is_Observer',
            field=models.BooleanField(default=False, help_text='Alleen observeren'),
        ),
    ]
