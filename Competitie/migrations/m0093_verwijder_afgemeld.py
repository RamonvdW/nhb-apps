# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from Competitie.definities import DEELNAME_NEE


def verwijder_afgemeld(apps, _):
    """ Verwijder de toevoeging [AFGEMELD] van de team naam """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    teamkamp_klas = apps.get_model('Competitie', 'KampioenschapTeam')

    print()
    for team in teamkamp_klas.objects.filter(team_naam__contains="AFGEMELD"):
        if team.team_naam.endswith(" [AFGEMELD]"):
            team.team_naam = team.team_naam[:-11]
            team.deelname = DEELNAME_NEE
            team.save(update_fields=['team_naam', 'deelname'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0092_non-optional'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(verwijder_afgemeld, migrations.RunPython.noop)
    ]

# end of file
