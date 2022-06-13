# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0006_mutatie_betaling'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='bestelling',
            name='status',
            field=models.CharField(choices=[('N', 'Nieuw'), ('B', 'Te betalen'), ('A', 'Afgerond')], default='N', max_length=1),
        ),
    ]

# end of file
