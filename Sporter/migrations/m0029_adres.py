# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0028_scheids'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sporter',
            name='adres_lat',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AddField(
            model_name='sporter',
            name='adres_lon',
            field=models.CharField(default='', max_length=10),
        ),
    ]

# end of file
