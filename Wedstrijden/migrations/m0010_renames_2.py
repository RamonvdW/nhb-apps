# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0009_renames_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='wedstrijd',
            name='uitslag',
        ),
        migrations.RenameField(
            model_name='wedstrijd',
            old_name='uitslag2',
            new_name='uitslag',
        ),
        migrations.RemoveField(
            model_name='competitiewedstrijduitslag',
            name='old',
        ),
        migrations.DeleteModel(
            name='WedstrijdUitslag',
        ),
    ]

# end of file
