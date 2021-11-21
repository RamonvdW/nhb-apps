# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Competitie.models import AG_NUL


def klassen_toevoegen(apps, _):
    """ voeg mid-flight de team wedstrijdklassen toe voor het RK/BK teams """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    comp_klas = apps.get_model('Competitie', 'CompetitieKlasse')

    # dupliceer alle team klassen voor RK/BK
    bulk = list()
    for klas in comp_klas.objects.exclude(team=None):
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
        migrations.RunPython(klassen_toevoegen)
    ]

# end of file
