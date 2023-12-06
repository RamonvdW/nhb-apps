# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Mailer', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='mailqueue',
            name='log',
            field=models.TextField(blank=True),
        ),
    ]

# end of file
