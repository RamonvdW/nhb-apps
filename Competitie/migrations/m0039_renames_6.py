# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0038_renames_5'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='deelcompetitieronde',
            name='plan',
        ),
        migrations.RenameField(
            model_name='deelcompetitieronde',
            old_name='plan2',
            new_name='plan',
        ),
        migrations.RemoveField(
            model_name='deelcompetitie',
            name='plan',
        ),
        migrations.RenameField(
            model_name='deelcompetitie',
            old_name='plan2',
            new_name='plan',
        ),
    ]

# end of file
