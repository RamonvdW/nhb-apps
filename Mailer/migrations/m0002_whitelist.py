# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    # volgorde afdwingen
    dependencies = [
        ('Mailer', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='mailqueue',
            name='is_blocked',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='mailqueue',
            name='aantal_pogingen',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='mailqueue',
            name='is_verstuurd',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
