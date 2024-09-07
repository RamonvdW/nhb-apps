# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0021_index'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='betaaltransactie',
            name='refund_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AlterField(
            model_name='betaaltransactie',
            name='refund_status',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
    ]

# end of file
