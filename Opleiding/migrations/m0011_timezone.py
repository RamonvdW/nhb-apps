# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleiding', 'm0010_remove_auto_now'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='opleidingafgemeld',
            name='wanneer_aangemeld',
            field=models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)),
        ),
    ]

# end of file
