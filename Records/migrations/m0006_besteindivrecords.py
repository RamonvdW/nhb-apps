# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Records', 'm0005_verbeterbaar'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BesteIndivRecords',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volgorde', models.PositiveIntegerField(default=0)),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('18', 'Indoor'), ('25', '25m 1pijl')], max_length=2)),
                ('soort_record', models.CharField(max_length=40)),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], max_length=1)),
                ('leeftijdscategorie', models.CharField(choices=[('M', 'Master'), ('S', 'Senior'), ('J', 'Junior'), ('C', 'Cadet'), ('U', 'Uniform (para)')], max_length=1)),
                ('materiaalklasse', models.CharField(choices=[('R', 'Recurve'), ('C', 'Compound'), ('BB', 'Barebow'), ('LB', 'Longbow'), ('IB', 'Instinctive bow')], max_length=2)),
                ('para_klasse', models.CharField(blank=True, max_length=20)),
                ('beste', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Records.IndivRecord')),
            ],
            options={
                'verbose_name': 'Beste individuele records',
                'verbose_name_plural': 'Beste individuele records',
            },
        ),
    ]

# end of file
