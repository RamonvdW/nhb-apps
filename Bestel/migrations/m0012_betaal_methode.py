# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0011_migratie_1'),
    ]

    # migratie functions
    operations = [
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_bic',
            field=models.CharField(blank=True, default='', max_length=11),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_heeft_mollie',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verkoper_iban',
            field=models.CharField(blank=True, default='', max_length=18),
        ),
    ]

# end of file
