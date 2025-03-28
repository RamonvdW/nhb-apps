# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleiding', 'm0009_afgemeld'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='opleidingafgemeld',
            name='wanneer_aangemeld',
            field=models.DateTimeField(default='2000-01-01'),
        ),
    ]

# end of file
