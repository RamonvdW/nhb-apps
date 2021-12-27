# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Competitie.models import AG_NUL


def clear_kampioenschapteam_klasse(apps, _):
    """ kampioenschap team klasse kan al ingesteld staan,
        maar moet leeg blijven totdat de RK/BK klassegrenzen vastgesteld zijn.
    """

    team_klas = apps.get_model('Competitie', 'KampioenschapTeam')

    for team in team_klas.objects.all():        # pragma: no cover
        team.klasse = None
        team.save(update_fields=['klasse'])
    # for


def klassen_toevoegen(apps, _):
    """ voeg mid-flight de team wedstrijdklassen toe voor het RK/BK teams """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    comp_klas = apps.get_model('Competitie', 'CompetitieKlasse')

    # dupliceer alle team klassen voor RK/BK
    bulk = list()
    for klas in comp_klas.objects.exclude(team=None):       # pragma: no cover
        klasse = comp_klas(
                        competitie=klas.competitie,
                        team=klas.team,
                        min_ag=AG_NUL,          # wordt later nog vastgesteld
                        is_voor_teams_rk_bk=True)
        bulk.append(klasse)
    # for

    comp_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0056_competitiemutatie_competitie'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitie',
            name='klassegrenzen_vastgesteld_rk_bk',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='competitieklasse',
            name='is_voor_teams_rk_bk',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(clear_kampioenschapteam_klasse),
        migrations.RunPython(klassen_toevoegen)
    ]

# end of file
