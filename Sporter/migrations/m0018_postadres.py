# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0017_pascode'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sporter',
            name='postadres_1',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='sporter',
            name='postadres_2',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='sporter',
            name='postadres_3',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]

# end of file
