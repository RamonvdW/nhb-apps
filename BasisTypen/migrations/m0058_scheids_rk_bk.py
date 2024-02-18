# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


INDIV_COMP_KRIJGT_SCHEIDS_RK = (1100, 1110, 1120,       # R
                                1200, 1210, 1220,       # C
                                1300, 1310)             # BB

INDIV_COMP_KRIJGT_SCHEIDS_BK = (1100, 1101, 1102, 1103, 1104, 1105, 1110, 1111, 1120, 1121,     # R
                                1200, 1201, 1210, 1211, 1220, 1221,                             # C
                                1300, 1301, 1310,                                               # BB
                                1400, 1401, 1410,                                               # TR
                                1500, 1501, 1510)                                               # LB

TEAM_COMP_KRIJGT_SCHEIDS_RK = (15,      # R
                               20,      # C
                               31)      # BB

TEAM_COMP_KRIJGT_SCHEIDS_BK = (15, 16, 17, 18, 19,      # R
                               20, 21,                  # C
                               31,                      # BB
                               41,                      # TR
                               50)                      # LB


def zet_scheids_rk_bk(apps, _):
    """ Zet de velden "krijgt_scheids_rk" en "krijgt_scheids_bk" voor de template competitie klassen """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')
    team_klas = apps.get_model('BasisTypen', 'TemplateCompetitieTeamKlasse')

    indiv_klas.objects.filter(volgorde__in=INDIV_COMP_KRIJGT_SCHEIDS_RK).update(krijgt_scheids_rk=True)
    team_klas.objects.filter(volgorde__in=TEAM_COMP_KRIJGT_SCHEIDS_RK).update(krijgt_scheids_rk=True)

    indiv_klas.objects.filter(volgorde__in=INDIV_COMP_KRIJGT_SCHEIDS_BK).update(krijgt_scheids_bk=True)
    team_klas.objects.filter(volgorde__in=TEAM_COMP_KRIJGT_SCHEIDS_BK).update(krijgt_scheids_bk=True)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0057_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='templatecompetitieindivklasse',
            name='krijgt_scheids_rk',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='templatecompetitieindivklasse',
            name='krijgt_scheids_bk',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='templatecompetitieteamklasse',
            name='krijgt_scheids_rk',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='templatecompetitieteamklasse',
            name='krijgt_scheids_bk',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(zet_scheids_rk_bk, reverse_code=migrations.RunPython.noop),
    ]

# end of file
