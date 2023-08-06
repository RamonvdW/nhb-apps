# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.migrations.m0054_squashed import (INDIV_VOLGORDE_18M__TITEL_NK, INDIV_VOLGORDE_25M__TITEL_NK,
                                                  TEAM_VOLGORDE__TITEL_NK)


def zet_titels(apps, _):
    """ default titel "Bondskampioen" aanpassen naar "Nederlands Kampioen" voor geselecteerde klassen """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')
    team_klas = apps.get_model('BasisTypen', 'TemplateCompetitieTeamKlasse')

    indiv_klas.objects.filter(niet_voor_rk_bk=True).update(titel_bk_18m='', titel_bk_25m='')

    for indiv in indiv_klas.objects.all():
        updated = list()

        if indiv.volgorde in INDIV_VOLGORDE_18M__TITEL_NK:
            indiv.titel_bk_18m = "Nederlands Kampioen"
            updated.append('titel_bk_18m')

        if indiv.volgorde in INDIV_VOLGORDE_25M__TITEL_NK:
            indiv.titel_bk_25m = "Nederlands Kampioen"
            updated.append('titel_bk_25m')

        if len(updated):
            indiv.save(update_fields=updated)
    # for

    for team in team_klas.objects.filter(volgorde__in=TEAM_VOLGORDE__TITEL_NK):
        team.titel_bk_18m = "Nederlands Kampioen"
        team.titel_bk_25m = "Nederlands Kampioen"
        team.save(update_fields=['titel_bk_18m', 'titel_bk_25m'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0054_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='templatecompetitieindivklasse',
            name='titel_bk_18m',
            field=models.CharField(default='Bondskampioen', max_length=30),
        ),
        migrations.AddField(
            model_name='templatecompetitieindivklasse',
            name='titel_bk_25m',
            field=models.CharField(default='Bondskampioen', max_length=30),
        ),
        migrations.AddField(
            model_name='templatecompetitieteamklasse',
            name='titel_bk_18m',
            field=models.CharField(default='Bondskampioen', max_length=30),
        ),
        migrations.AddField(
            model_name='templatecompetitieteamklasse',
            name='titel_bk_25m',
            field=models.CharField(default='Bondskampioen', max_length=30),
        ),
        migrations.RunPython(zet_titels, migrations.RunPython.noop)
    ]

# end of file
