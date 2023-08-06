# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0096_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='kampioenschapsporterboog',
            old_name='result_teamscore_1',
            new_name='result_rk_teamscore_1',
        ),
        migrations.RenameField(
            model_name='kampioenschapsporterboog',
            old_name='result_teamscore_2',
            new_name='result_rk_teamscore_2',
        ),
    ]

# end of file
