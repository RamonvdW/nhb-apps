# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleiding', 'm0004_periode'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='opleidinginschrijving',
            name='status',
            field=models.CharField(choices=[('I', 'Inschrijven'), ('R', 'Reservering'), ('B', 'Besteld'),
                                            ('D', 'Definitief')],
                                   default='I', max_length=2),
        ),
    ]

# end of file
