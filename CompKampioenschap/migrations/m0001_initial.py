# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('GoogleDrive', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SheetStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gewijzigd_op', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0,
                                                                                tzinfo=datetime.timezone.utc))),
                ('gewijzigd_door', models.CharField(default='', max_length=100)),
                ('bekeken_op', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0,
                                                                              tzinfo=datetime.timezone.utc))),
                ('wedstrijd_fase', models.CharField(default='', max_length=100)),
                ('bevat_scores', models.BooleanField(default=False)),
                ('uitslag_is_compleet', models.BooleanField(default=False)),
                ('uitslag_ingelezen_op', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0,
                                                                                        tzinfo=datetime.timezone.utc))),
                ('aantal_deelnemers', models.PositiveSmallIntegerField(default=0)),
                ('bestand', models.ForeignKey(on_delete=models.deletion.CASCADE, to='GoogleDrive.bestand')),
            ],
            options={
                'verbose_name': 'Sheet status',
                'verbose_name_plural': 'Sheet status',
            },
        ),
    ]

# end of file
