# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0019_bedragen'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='betaaltransactie',
            name='bedrag_refund',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=7),
        ),
        migrations.AddField(
            model_name='betaaltransactie',
            name='refund_id',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AddField(
            model_name='betaaltransactie',
            name='refund_status',
            field=models.CharField(default='', max_length=15),
        ),
    ]

# end of file
