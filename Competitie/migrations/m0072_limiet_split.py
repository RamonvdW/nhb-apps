# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def migreer_limieten(apps, _):
    """ Split DeelcompetitieKlasseLimiet op in DeelcompetitieIndiv/TeamsKlasseLimiet """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    limiet_klas = apps.get_model('Competitie', 'DeelcompetitieKlasseLimiet')
    indiv_klas = apps.get_model('Competitie', 'DeelcompetitieIndivKlasseLimiet')
    team_klas = apps.get_model('Competitie', 'DeelcompetitieTeamKlasseLimiet')

    bulk_indiv = list()
    bulk_team = list()

    for limiet in (limiet_klas                                  # pragma: no cover
                   .objects
                   .select_related('deelcompetitie',
                                   'indiv_klasse',
                                   'team_klasse')
                   .all()):
        if limiet.indiv_klasse:
            indiv = indiv_klas(
                        deelcompetitie=limiet.deelcompetitie,
                        indiv_klasse=limiet.indiv_klasse,
                        limiet=limiet.limiet)
            bulk_indiv.append(indiv)
        else:
            team = team_klas(
                        deelcompetitie=limiet.deelcompetitie,
                        team_klasse=limiet.team_klasse,
                        limiet=limiet.limiet)
            bulk_team.append(team)
    # for

    indiv_klas.objects.bulk_create(bulk_indiv)
    team_klas.objects.bulk_create(bulk_team)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0071_matches'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='DeelcompetitieTeamKlasseLimiet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=24)),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('team_klasse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieteamklasse')),
            ],
            options={
                'verbose_name': 'Deelcompetitie TeamKlasse Limiet',
                'verbose_name_plural': 'Deelcompetitie TeamKlasse Limieten',
            },
        ),
        migrations.CreateModel(
            name='DeelcompetitieIndivKlasseLimiet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=24)),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('indiv_klasse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieindivklasse')),
            ],
            options={
                'verbose_name': 'Deelcompetitie IndivKlasse Limiet',
                'verbose_name_plural': 'Deelcompetitie IndivKlasse Limieten',
            },
        ),
        migrations.RunPython(migreer_limieten),
        migrations.DeleteModel(
            name='DeelcompetitieKlasseLimiet',
        ),
    ]

# end of file
