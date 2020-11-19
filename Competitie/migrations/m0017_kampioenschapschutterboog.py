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
        ('Schutter', 'm0006_squashed'),
        ('Competitie', 'm0016_heeft_deelnemerslijst'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='KampioenschapSchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kampioen_label', models.CharField(max_length=50, default='', blank=True)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('deelname_bevestigd', models.BooleanField(default=False)),
                ('is_afgemeld', models.BooleanField(default=False)),
                ('gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.DeelCompetitie')),
                ('bij_vereniging', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbVereniging', blank=True, null=True)),
                ('klasse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.CompetitieKlasse')),
                ('schutterboog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Schutter.SchutterBoog')),
                ('bevestiging_gevraagd_op', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Kampioenschap Schutterboog',
                'verbose_name_plural': 'Kampioenschap Schuttersboog',
            },
        ),
    ]

# end of file
