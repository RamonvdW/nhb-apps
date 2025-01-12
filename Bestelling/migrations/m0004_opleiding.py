# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0003_squashed'),
        ('Opleiding', 'm0002_opleiding'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestellingmutatie',
            name='opleiding_deelnemer',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Opleiding.opleidingdeelnemer'),
        ),
        migrations.AddField(
            model_name='bestellingproduct',
            name='opleiding_deelnemer',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Opleiding.opleidingdeelnemer'),
        ),
    ]

# end of file
