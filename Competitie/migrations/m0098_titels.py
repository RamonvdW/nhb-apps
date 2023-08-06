# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_titels(apps, _):
    """ BK titels (Bondskampioen of Nederlands Kampioen) overnemen uit de BasisTypen """

    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        indiv_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')
        comp_indiv_klas = apps.get_model('Competitie', 'CompetitieIndivKlasse')

        volgorde2titels = dict()     # [volgorde] = (titel 18m, titel 25m)
        for indiv in indiv_klas.objects.all():                                          # pragma: no cover
            volgorde2titels[indiv.volgorde] = (indiv.titel_bk_18m, indiv.titel_bk_25m)
        # for

        for indiv in comp_indiv_klas.objects.select_related('competitie').all():        # pragma: no cover

            titel_18m, titel_25m = volgorde2titels[indiv.volgorde]

            if indiv.competitie.afstand == '18':
                indiv.titel_bk = titel_18m
            else:
                indiv.titel_bk = titel_25m

            indiv.save(update_fields=['titel_bk'])
        # for

    if True:
        team_klas = apps.get_model('BasisTypen', 'TemplateCompetitieTeamKlasse')
        comp_team_klas = apps.get_model('Competitie', 'CompetitieTeamKlasse')

        volgorde2titels = dict()      # [volgorde] = (titel 18m, titel 25m)
        for team in team_klas.objects.all():                                          # pragma: no cover
            titels = (team.titel_bk_18m, team.titel_bk_25m)
            volgorde2titels[team.volgorde] = titels
            volgorde2titels[team.volgorde + 100] = titels       # +100 is voor RK/BK instantie
        # for

        for team in comp_team_klas.objects.filter(is_voor_teams_rk_bk=True).select_related('competitie'):   # pragma: no cover
            titel_18m, titel_25m = volgorde2titels[team.volgorde]

            if team.competitie.afstand == '18':
                team.titel_bk = titel_18m
            else:
                team.titel_bk = titel_25m

            team.save(update_fields=['titel_bk'])
        # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0097_renames'),
        ('BasisTypen', 'm0055_titels'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitieindivklasse',
            name='titel_bk',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AddField(
            model_name='competitieteamklasse',
            name='titel_bk',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.RunPython(zet_titels, migrations.RunPython.noop)
    ]

# end of file
