# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0050_rondeteam_feitelijk'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='regiocompetitieteam',
            name='aanvangsgemiddelde',
            field=models.DecimalField(decimal_places=1, default=0.0, max_digits=4),
        ),
    ]

# end of file
