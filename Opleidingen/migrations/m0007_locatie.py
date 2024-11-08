# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Locatie', 'm0009_squashed'),
        ('Opleidingen', 'm0006_correcties'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='opleidingmoment',
            name='locatie',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                    to='Locatie.evenementlocatie'),
        ),
    ]

# end of file
