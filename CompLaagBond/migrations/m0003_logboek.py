# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('CompLaagBond', 'm0002_rk_result_rank'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='teambk',
            name='logboek',
            field=models.TextField(blank=True),
        ),
    ]

# end of file
