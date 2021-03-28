# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0031_remove_3p'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='regiocompetitieteam',
            old_name='vaste_schutters',
            new_name='gekoppelde_schutters',
        ),
        migrations.RemoveField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_team_type',
        ),
    ]

# end of file
