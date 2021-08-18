# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0019_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Speelsterkte',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('beschrijving', models.CharField(max_length=50)),
                ('discipline', models.CharField(max_length=50)),
                ('category', models.CharField(max_length=50)),
                ('volgorde', models.PositiveSmallIntegerField()),
                ('lid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='NhbStructuur.nhblid')),
            ],
        ),
    ]

# end of file
