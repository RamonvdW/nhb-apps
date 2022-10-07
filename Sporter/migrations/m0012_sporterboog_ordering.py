# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0011_geboorteplaats_telefoon'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='sporterboog',
            options={'ordering': ['sporter__lid_nr', 'boogtype__volgorde'], 'verbose_name': 'SporterBoog', 'verbose_name_plural': 'SporterBoog'},
        ),
    ]

# end of file
