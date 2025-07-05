# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0031_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='sporter',
            name='email',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]

# end of file
