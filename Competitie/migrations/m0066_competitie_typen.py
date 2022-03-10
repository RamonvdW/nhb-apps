# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_competitie_typen(apps, _):

    comp_klas = apps.get_model('Competitie', 'Competitie')
    klasse_klas = apps.get_model('Competitie', 'CompetitieKlasse')

    for comp in comp_klas.objects.all():                # pragma: no cover
        boogtypen_pks = list()
        teamtypen_pks = list()

        for klasse in (klasse_klas
                       .objects
                       .filter(competitie=comp)
                       .select_related('indiv',
                                       'indiv__boogtype',
                                       'team',
                                       'team__team_type')):

            if klasse.indiv:
                boogtype_pk = klasse.indiv.boogtype.pk
                if boogtype_pk not in boogtypen_pks:
                    boogtypen_pks.append(boogtype_pk)

            if klasse.team:
                teamtype_pk = klasse.team.team_type.pk
                if teamtype_pk not in teamtypen_pks:
                    teamtypen_pks.append(teamtype_pk)
        # for

        comp.boogtypen.set(boogtypen_pks)
        comp.teamtypen.set(teamtypen_pks)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0028_squashed'),
        ('Competitie', 'm0065_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitie',
            name='boogtypen',
            field=models.ManyToManyField(to='BasisTypen.BoogType'),
        ),
        migrations.AddField(
            model_name='competitie',
            name='teamtypen',
            field=models.ManyToManyField(to='BasisTypen.TeamType'),
        ),
        migrations.RunPython(zet_competitie_typen)
    ]

# end of file
