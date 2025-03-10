# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models, migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Evenement', 'm0003_bestelling'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='evenementinschrijving',
            name='status',
            field=models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'),
                                            ('D', 'Definitief'), ('A', 'Afgemeld')],
                                   default='R', max_length=2),
        ),
    ]

# end of file
