# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0110_scheids_rk_bk'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapsporterboog',
            name='logboek',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='regiocompetitierondeteam',
            name='logboek',
            field=models.TextField(blank=True),
        ),
    ]

# end of file
