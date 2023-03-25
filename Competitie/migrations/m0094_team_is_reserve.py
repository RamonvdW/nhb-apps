# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_is_reserve(apps, _):
    """ zet het nieuwe veld is_reserve (default=False) """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_klas = apps.get_model('Competitie', 'KampioenschapTeam')
    limiet_klas = apps.get_model('Competitie', 'KampioenschapTeamKlasseLimiet')

    klasse2limiet = dict()     # [(kampioenschap.pk, klasse.pk)] = limiet
    for limiet in limiet_klas.objects.select_related('kampioenschap', 'team_klasse').all():
        tup = (limiet.kampioenschap.pk, limiet.team_klasse.pk)
        klasse2limiet[tup] = limiet.limiet
    # for

    for team in team_klas.objects.exclude(team_klasse=None).select_related('kampioenschap', 'team_klasse').all():
        tup = (team.kampioenschap.pk, team.team_klasse.pk)
        try:
            limiet = klasse2limiet[tup]
        except KeyError:
            limiet = 12 if "ERE" in team.team_klasse.beschrijving else 8
            klasse2limiet[tup] = limiet

        if team.rank > limiet:
            team.is_reserve = True
            team.save(update_fields=['is_reserve'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0093_verwijder_afgemeld'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapteam',
            name='is_reserve',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(zet_is_reserve, migrations.RunPython.noop)
    ]

# end of file
