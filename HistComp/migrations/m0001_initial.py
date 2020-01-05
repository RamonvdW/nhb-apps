# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HistCompetitie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seizoen', models.CharField(max_length=9)),
                ('comp_type', models.CharField(choices=[('18', '18m Indoor'), ('25', '25m1pijl')], max_length=2)),
                ('klasse', models.CharField(max_length=20)),
                ('is_team', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Historie competitie',
                'verbose_name_plural': 'Historie competitie',
            },
        ),
        migrations.CreateModel(
            name='HistCompetitieTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subklasse', models.CharField(max_length=20)),
                ('rank', models.PositiveIntegerField()),
                ('vereniging_nr', models.PositiveIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('team_nr', models.PositiveSmallIntegerField()),
                ('totaal_ronde1', models.PositiveIntegerField()),
                ('totaal_ronde2', models.PositiveIntegerField()),
                ('totaal_ronde3', models.PositiveIntegerField()),
                ('totaal_ronde4', models.PositiveIntegerField()),
                ('totaal_ronde5', models.PositiveIntegerField()),
                ('totaal_ronde6', models.PositiveIntegerField()),
                ('totaal_ronde7', models.PositiveIntegerField()),
                ('totaal', models.PositiveIntegerField()),
                ('gemiddelde', models.DecimalField(decimal_places=1, max_digits=5)),
                ('histcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HistComp.HistCompetitie')),
            ],
            options={
                'verbose_name': 'Historie team competitie',
                'verbose_name_plural': 'Historie team competitie',
            },
        ),
        migrations.CreateModel(
            name='HistCompetitieIndividueel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveIntegerField()),
                ('schutter_nr', models.PositiveIntegerField()),
                ('schutter_naam', models.CharField(max_length=50)),
                ('vereniging_nr', models.PositiveIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('boogtype', models.CharField(max_length=5)),
                ('score1', models.PositiveIntegerField()),
                ('score2', models.PositiveIntegerField()),
                ('score3', models.PositiveIntegerField()),
                ('score4', models.PositiveIntegerField()),
                ('score5', models.PositiveIntegerField()),
                ('score6', models.PositiveIntegerField()),
                ('score7', models.PositiveIntegerField()),
                ('totaal', models.PositiveIntegerField()),
                ('gemiddelde', models.DecimalField(decimal_places=3, max_digits=5)),
                ('histcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HistComp.HistCompetitie')),
            ],
            options={
                'verbose_name': 'Historie individuele competitie',
                'verbose_name_plural': 'Historie individuele competitie',
            },
        ),
    ]

# end of file

