# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0047_team_ronde'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='CompetitieMutatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('mutatie', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('door', models.CharField(default='', max_length=50)),
                ('cut_oud', models.PositiveSmallIntegerField(default=0)),
                ('cut_nieuw', models.PositiveSmallIntegerField(default=0)),
                ('deelcompetitie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('deelnemer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.kampioenschapschutterboog')),
                ('klasse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse')),
            ],
            options={
                'verbose_name': 'Competitie mutatie',
            },
        ),
        migrations.AddField(
            model_name='competitietaken',
            name='hoogste_mutatie2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='Competitie.competitiemutatie'),
        ),
        migrations.RemoveField(
            model_name='competitietaken',
            name='hoogste_mutatie',
        ),
        migrations.RenameField(
            model_name='competitietaken',
            old_name='hoogste_mutatie2',
            new_name='hoogste_mutatie',
        ),
        migrations.DeleteModel(
            name='KampioenschapMutatie',
        ),
    ]

# end of file
