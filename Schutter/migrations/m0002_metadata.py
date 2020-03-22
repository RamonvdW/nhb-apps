# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Schutter', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='schutterboog',
            options={'verbose_name': 'SchutterBoog', 'verbose_name_plural': 'SchuttersBoog'},
        ),
    ]

# end of file
