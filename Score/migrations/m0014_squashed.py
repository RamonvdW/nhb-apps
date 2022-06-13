# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Score', 'm0011_squashed'),
                ('Score', 'm0012_score_geen'),
                ('Score', 'm0013_indexes')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
        ('Sporter', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('waarde', models.PositiveSmallIntegerField()),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('type', models.CharField(choices=[('S', 'Score'), ('I', 'Indiv AG'), ('T', 'Team AG'), ('G', 'Geen score')], default='S', max_length=1)),
                ('sporterboog', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='Sporter.sporterboog')),
            ],
        ),
        migrations.CreateModel(
            name='ScoreHist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oude_waarde', models.PositiveSmallIntegerField()),
                ('nieuwe_waarde', models.PositiveSmallIntegerField()),
                ('notitie', models.CharField(max_length=100)),
                ('door_account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Account.Account')),
                ('score', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Score.score')),
                ('when', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='score',
            constraint=models.UniqueConstraint(condition=models.Q(('type', 'G')), fields=('sporterboog', 'type'), name='max 1 geen score per sporterboog'),
        ),
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['afstand_meter'], name='Score_score_afstand_c4e380_idx'),
        ),
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['type'], name='Score_score_type_573ac6_idx'),
        ),
        migrations.AddIndex(
            model_name='scorehist',
            index=models.Index(fields=['when'], name='Score_score_when_9c19cd_idx'),
        ),
    ]

# end of file
