# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_kampioenschap(apps, _):
    """ Zet de een aantal klassen om van deelcompetitie naar kampioenschap """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    deelkamp_klas = apps.get_model('Competitie', 'DeelKampioenschap')
    kamp_team_klas = apps.get_model('Competitie', 'KampioenschapTeam')
    kamp_indiv_klas = apps.get_model('Competitie', 'KampioenschapSporterBoog')
    limiet_team_klas = apps.get_model('Competitie', 'KampioenschapTeamKlasseLimiet')
    limiet_indiv_klas = apps.get_model('Competitie', 'KampioenschapIndivKlasseLimiet')

    deelcomp2deelkamp = dict()      # [DeelCompetitie.pk] = DeelKampioenschap

    for deelkamp in deelkamp_klas.objects.select_related('old_deelcomp').all():
        deelcomp2deelkamp[deelkamp.old_deelcomp.pk] = deelkamp
    # for

    for kamp in kamp_team_klas.objects.select_related('deelcompetitie').all():
        kamp.kampioenschap = deelcomp2deelkamp[kamp.deelcompetitie.pk]
        kamp.save(update_fields=['kampioenschap'])
    # for

    for kamp in kamp_indiv_klas.objects.select_related('deelcompetitie').all():
        kamp.kampioenschap = deelcomp2deelkamp[kamp.deelcompetitie.pk]
        kamp.save(update_fields=['kampioenschap'])
    # for

    for limiet in limiet_team_klas.objects.select_related('deelcompetitie').all():
        limiet.kampioenschap = deelcomp2deelkamp[limiet.deelcompetitie.pk]
        limiet.save(update_fields=['kampioenschap'])
    # for

    for limiet in limiet_indiv_klas.objects.select_related('deelcompetitie').all():
        limiet.kampioenschap = deelcomp2deelkamp[limiet.deelcompetitie.pk]
        limiet.save(update_fields=['kampioenschap'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0080_kampioenschap_1'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapsporterboog',
            name='kampioenschap',
            field=models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Competitie.deelkampioenschap'),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='kampioenschap',
            field=models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Competitie.deelkampioenschap'),
        ),
        migrations.RenameModel(
            old_name='DeelcompetitieIndivKlasseLimiet',
            new_name='KampioenschapIndivKlasseLimiet',
        ),
        migrations.RenameModel(
            old_name='DeelcompetitieTeamKlasseLimiet',
            new_name='KampioenschapTeamKlasseLimiet',
        ),
        migrations.AddField(
            model_name='kampioenschapteamklasselimiet',
            name='kampioenschap',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelkampioenschap', null=True),
        ),
        migrations.AddField(
            model_name='kampioenschapindivklasselimiet',
            name='kampioenschap',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelkampioenschap', null=True),
        ),
        migrations.AlterModelOptions(
            name='kampioenschapindivklasselimiet',
            options={'verbose_name': 'Kampioenschap IndivKlasse Limiet',
                     'verbose_name_plural': 'Kampioenschap IndivKlasse Limieten'},
        ),
        migrations.AlterModelOptions(
            name='kampioenschapteamklasselimiet',
            options={'verbose_name': 'Kampioenschap TeamKlasse Limiet',
                     'verbose_name_plural': 'Kampioenschap TeamKlasse Limieten'},
        ),
        migrations.RunPython(migreer_kampioenschap, reverse_code=migrations.RunPython.noop)
    ]

# end of file
