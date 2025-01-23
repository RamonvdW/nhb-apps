# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0004_opleiding'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='bestellingmutatie',
            old_name='opleiding_deelnemer',
            new_name='opleiding_inschrijving',
        ),
        migrations.RenameField(
            model_name='bestellingproduct',
            old_name='opleiding_deelnemer',
            new_name='opleiding_inschrijving',
        ),
    ]

# end of file
