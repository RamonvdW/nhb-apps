# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Evenement', 'm0005_workshops'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='evenement',
            old_name='workshop_keuze',
            new_name='workshop_opties',
        ),
        migrations.AddField(
            model_name='evenement',
            name='prijs_euro_gast',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5),
        ),
    ]

# end of file
