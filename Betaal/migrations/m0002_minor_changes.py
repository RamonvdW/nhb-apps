# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='betaaltransactie',
            options={'verbose_name': 'Betaal transactie', 'verbose_name_plural': 'Betaal transacties'},
        ),
        migrations.AlterField(
            model_name='betaalinstellingenvereniging',
            name='mollie_api_key',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]

# end of file
