# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0094_team_is_reserve'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='competitieindivklasse',
            old_name='is_voor_rk_bk',
            new_name='is_ook_voor_rk_bk',
        ),
    ]

# end of file
