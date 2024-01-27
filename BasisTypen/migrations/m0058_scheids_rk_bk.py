# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


INDIV_COMP_KRIJGT_SCHEIDS = (1100, 1110, 1120, 1200, 1210, 1220, 1300, 1310)
TEAM_COMP_KRIJGT_SCHEIDS = (15, 20, 31)


def zet_scheids_rk_bk(apps, _):
    """ Zet het veld "krijgt_scheids_rk_bk" voor de template competitie klassen """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')
    team_klas = apps.get_model('BasisTypen', 'TemplateCompetitieTeamKlasse')

    indiv_klas.objects.filter(volgorde__in=INDIV_COMP_KRIJGT_SCHEIDS).update(krijgt_scheids_rk_bk=True)
    team_klas.objects.filter(volgorde__in=TEAM_COMP_KRIJGT_SCHEIDS).update(krijgt_scheids_rk_bk=True)


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
            name='krijgt_scheids_rk_bk',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='templatecompetitieteamklasse',
            name='krijgt_scheids_rk_bk',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(zet_scheids_rk_bk, reverse_code=migrations.RunPython.noop),
    ]

# end of file
