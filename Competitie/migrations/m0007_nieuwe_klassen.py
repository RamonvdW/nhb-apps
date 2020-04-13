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
        ('Schutter', 'm0003_add_nhblid'),
        ('NhbStructuur', 'm0009_migrate_nhblid_account'),
        ('BasisTypen', 'm0008_vereenvoudiging'),
        ('Competitie', 'm0006_delete-competitiewedstrijdklasse'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='CompetitieKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
                ('competitie', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='Competitie.Competitie')),
                ('indiv', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.IndivWedstrijdklasse')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.TeamWedstrijdklasse')),
            ],
        ),
        migrations.CreateModel(
            name='RegioCompetitieSchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_handmatig_ag', models.BooleanField(default=False)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, max_digits=5)),
                ('score1', models.PositiveIntegerField()),
                ('score2', models.PositiveIntegerField()),
                ('score3', models.PositiveIntegerField()),
                ('score4', models.PositiveIntegerField()),
                ('score5', models.PositiveIntegerField()),
                ('score6', models.PositiveIntegerField()),
                ('score7', models.PositiveIntegerField()),
                ('totaal', models.PositiveIntegerField()),
                ('laagste_score_nr', models.PositiveIntegerField(default=0)),
                ('gemiddelde', models.DecimalField(decimal_places=3, max_digits=5)),
                ('bij_vereniging', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbVereniging')),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.DeelCompetitie')),
                ('klasse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.CompetitieKlasse')),
                ('schutterboog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Schutter.SchutterBoog')),
            ],
        ),
    ]

# end of file
