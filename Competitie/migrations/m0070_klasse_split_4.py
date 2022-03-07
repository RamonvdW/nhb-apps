# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0069_klasse_split_3'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='competitiemutatie',
            name='klasse',
        ),
        migrations.RemoveField(
            model_name='deelcompetitieklasselimiet',
            name='klasse',
        ),
        migrations.RemoveField(
            model_name='kampioenschapschutterboog',
            name='klasse',
        ),
        migrations.RemoveField(
            model_name='kampioenschapteam',
            name='klasse',
        ),
        migrations.RemoveField(
            model_name='regiocompetitieschutterboog',
            name='klasse',
        ),
        migrations.RemoveField(
            model_name='regiocompetitieteam',
            name='klasse',
        ),
    ]

# end of file
