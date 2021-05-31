# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0036_renames_3'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_gekozen_wedstrijden',
        ),
        migrations.RenameField(
            model_name='regiocompetitieschutterboog',
            old_name='inschrijf_gekozen_wedstrijden2',
            new_name='inschrijf_gekozen_wedstrijden',
        ),
    ]

# end of file
