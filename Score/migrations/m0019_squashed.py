# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0023_squashed'),
        ('BasisTypen', 'm0054_squashed'),
        ('Sporter', 'm0021_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('waarde', models.PositiveSmallIntegerField()),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('type', models.CharField(choices=[('S', 'Score'), ('G', 'Geen score')], default='S', max_length=1)),
                ('sporterboog', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
            ],
        ),
        migrations.AddConstraint(
            model_name='score',
            constraint=models.UniqueConstraint(condition=models.Q(('type', 'G')), fields=('sporterboog', 'type'), name='max 1 geen score per sporterboog'),
        ),
        migrations.CreateModel(
            name='ScoreHist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oude_waarde', models.PositiveSmallIntegerField()),
                ('nieuwe_waarde', models.PositiveSmallIntegerField()),
                ('notitie', models.CharField(max_length=100)),
                ('door_account', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
                ('score', models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Score.score')),
                ('when', models.DateTimeField(auto_now_add=True)),
            ],
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
        migrations.CreateModel(
            name='Uitslag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_score', models.PositiveSmallIntegerField()),
                ('afstand', models.PositiveSmallIntegerField()),
                ('is_bevroren', models.BooleanField(default=False)),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
            ],
            options={
                'verbose_name': 'Uitslag',
                'verbose_name_plural': 'Uitslagen',
            },
        ),
        migrations.CreateModel(
            name='Aanvangsgemiddelde',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doel', models.CharField(choices=[('i', 'Individueel'), ('t', 'Teamcompetitie')], default='i', max_length=1)),
                ('waarde', models.DecimalField(decimal_places=3, max_digits=6)),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('boogtype', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
            ],
        ),
        migrations.CreateModel(
            name='AanvangsgemiddeldeHist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('oude_waarde', models.DecimalField(decimal_places=3, max_digits=6)),
                ('nieuwe_waarde', models.DecimalField(decimal_places=3, max_digits=6)),
                ('notitie', models.CharField(max_length=100)),
                ('ag', models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, related_name='ag_hist', to='Score.aanvangsgemiddelde')),
                ('door_account', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
            ],
        ),
        migrations.AddIndex(
            model_name='aanvangsgemiddeldehist',
            index=models.Index(fields=['when'], name='Score_aanva_when_9de5cf_idx'),
        ),
    ]

# end of file
