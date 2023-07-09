# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0038_remove_max_dt_per_baan'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='wedstrijd',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA')], default='W', max_length=1),
        ),
    ]

# end of file
