# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0022_pas_code'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sporter',
            name='is_gast',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
