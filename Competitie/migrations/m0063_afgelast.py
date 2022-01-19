# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0062_indexes'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitie',
            name='bk_afgelast_bericht',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='competitie',
            name='bk_is_afgelast',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='competitie',
            name='rk_afgelast_bericht',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='competitie',
            name='rk_is_afgelast',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
