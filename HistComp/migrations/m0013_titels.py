# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0012_no_defaults'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='histkampindiv',
            name='titel_code_bk',
            field=models.CharField(choices=[(' ', 'None'), ('R', 'RK'), ('B', 'BK'), ('N', 'NK')], default=' ', max_length=1),
        ),
        migrations.AddField(
            model_name='histkampindiv',
            name='titel_code_rk',
            field=models.CharField(choices=[(' ', 'None'), ('R', 'RK'), ('B', 'BK'), ('N', 'NK')], default=' ', max_length=1),
        ),
        migrations.AddField(
            model_name='histkampteam',
            name='titel_code',
            field=models.CharField(choices=[(' ', 'None'), ('R', 'RK'), ('B', 'BK'), ('N', 'NK')], default=' ', max_length=1),
        ),
        # er zijn nog geen historische uitslagen RK/BK waarvoor we een titel moeten zetten
    ]

# end of file
