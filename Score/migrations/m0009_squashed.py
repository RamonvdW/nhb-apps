# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
        ('Schutter', 'm0010_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('waarde', models.PositiveSmallIntegerField()),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('schutterboog', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Schutter.schutterboog')),
                ('type', models.CharField(choices=[('S', 'Score'), ('I', 'Indiv AG'), ('T', 'Team AG')], default='S', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='ScoreHist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oude_waarde', models.PositiveSmallIntegerField()),
                ('nieuwe_waarde', models.PositiveSmallIntegerField()),
                ('notitie', models.CharField(max_length=100)),
                ('door_account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                   to=settings.AUTH_USER_MODEL)),
                ('score', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Score.score')),
                ('when', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

# end of file
