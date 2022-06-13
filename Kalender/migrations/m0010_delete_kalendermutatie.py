# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0009_combi_korting'),
    ]

    # migratie functies
    operations = [
        migrations.DeleteModel(
            name='KalenderMutatie',
        ),
        migrations.AlterField(
            model_name='kalenderinschrijving',
            name='status',
            field=models.CharField(
                choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief'), ('A', 'Afgemeld')], default='R',
                max_length=2),
        ),
    ]

# end of file
