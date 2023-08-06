# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0099_renames'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='kampioenschap',
            name='is_klaar_indiv',
        ),
        migrations.RemoveField(
            model_name='kampioenschap',
            name='is_klaar_teams',
        ),
    ]

# end of file
