# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Schutter', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='schutterboog',
            name='account',
        ),
        migrations.RemoveField(
            model_name='schuttervoorkeuren',
            name='account',
        ),
    ]

# end of file
