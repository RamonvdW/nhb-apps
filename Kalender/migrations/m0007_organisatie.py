# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'Nationaal'), ('F', 'IFAA')], default='W', max_length=1),
        ),
    ]

# end of file
