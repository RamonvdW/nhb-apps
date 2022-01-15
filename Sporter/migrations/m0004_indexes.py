# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0003_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddIndex(
            model_name='sporterboog',
            index=models.Index(fields=['voor_wedstrijd'], name='Sporter_spo_voor_we_c6b357_idx'),
        ),
    ]

# end of file
