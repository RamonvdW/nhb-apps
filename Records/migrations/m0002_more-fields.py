# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Records', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='indivrecord',
            name='max_score',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='indivrecord',
            name='x_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='indivrecord',
            name='score_notitie',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]

# end of file
