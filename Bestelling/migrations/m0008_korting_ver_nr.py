# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0007_remove_product'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestellingregel',
            name='korting_ver_nr',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]

# end of file
