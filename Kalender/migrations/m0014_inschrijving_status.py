# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0013_code_uitgever'),
    ]

    operations = [
        migrations.AddField(
            model_name='kalenderinschrijving',
            name='status',
            field=models.CharField(choices=[('R', 'Reservering'), ('D', 'Definitief'), ('A', 'Afgemeld')], default='R', max_length=2),
        ),
        migrations.RemoveField(
            model_name='kalenderinschrijving',
            name='betaling_voldaan',
        ),
        migrations.AddField(
            model_name='kalenderinschrijving',
            name='ontvangen_euro',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5),
        ),
        migrations.AddField(
            model_name='kalenderinschrijving',
            name='retour_euro',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5),
        ),
    ]

# end of file
