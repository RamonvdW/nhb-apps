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
        ('Competitie', 'm0007_nieuwe_klassen'),
        ('Wedstrijden', 'm0002_wedstrijdenplan'),
        ('NhbStructuur', 'm0011_clusters'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='deelcompetitie',
            name='plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdenPlan'),
        ),
        migrations.CreateModel(
            name='DeelcompetitieRonde',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_nr', models.PositiveSmallIntegerField()),
                ('beschrijving', models.CharField(max_length=20)),
                ('cluster', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbCluster')),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.DeelCompetitie')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdenPlan')),
            ],
        ),
    ]

# end of file
