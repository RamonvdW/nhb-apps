# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0009_migrate_functie_nhblid_part1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='account',
            name='nhblid',
        ),
        migrations.RemoveField(
            model_name='account',
            name='functies',
        ),
    ]

# end of file
