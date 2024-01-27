# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_scheids_rk_bk(apps, _):
    """ Indoor wedstrijden kunnen scheidsrechter krijgen voor RK/BK aan de hand van de template """

    basis_indiv_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')
    volgordes = list(basis_indiv_klas.objects.filter(krijgt_scheids_rk_bk=True).values_list('volgorde', flat=True))
    indiv_klas = apps.get_model('Competitie', 'CompetitieIndivKlasse')
    indiv_klas.objects.filter(volgorde__in=volgordes, competitie__afstand='18').update(krijgt_scheids_rk_bk=True)

    basis_team_klas = apps.get_model('BasisTypen', 'TemplateCompetitieTeamKlasse')
    volgordes = list(basis_team_klas.objects.filter(krijgt_scheids_rk_bk=True).values_list('volgorde', flat=True))
    volgordes = [volgorde + 100 for volgorde in volgordes]  # RK/BK klassen hebben aparte nummering
    team_klas = apps.get_model('Competitie', 'CompetitieTeamKlasse')
    team_klas.objects.filter(volgorde__in=volgordes, competitie__afstand='18').update(krijgt_scheids_rk_bk=True)


def zet_aantal_scheids(apps, _):
    """ als een de team/indiv klassen de vlag krijgt_scheids_rk_bk=True heeft dan krijgt de CompetitieMatch
        aantal_scheids=1, anders 0.
    """

    match_klas = apps.get_model('Competitie', 'CompetitieMatch')
    indiv_klas = apps.get_model('Competitie', 'CompetitieIndivKlasse')
    team_klas = apps.get_model('Competitie', 'CompetitieTeamKlasse')
    kamp_klas = apps.get_model('Competitie', 'Kampioenschap')

    # (is default)
    # match_klas.objects.all().update(aantal_scheids=0)

    # vind the matches in de omgekeerde volgorde
    match_pks = list()
    for indiv in indiv_klas.objects.filter(krijgt_scheids_rk_bk=True).prefetch_related('competitiematch_set'):
        match_pks.extend(list(indiv.competitiematch_set.values_list('pk', flat=True)))
    # for

    for team in team_klas.objects.filter(krijgt_scheids_rk_bk=True).prefetch_related('competitiematch_set'):
        match_pks.extend(list(team.competitiematch_set.values_list('pk', flat=True)))
    # for

    need_sr_pks = list()
    for kamp in kamp_klas.objects.all().prefetch_related('rk_bk_matches'):
        pks = list(kamp.rk_bk_matches.values_list('pk', flat=True))
        for pk in pks:
            if pk in match_pks:
                need_sr_pks.append(pk)
        # for
    # for

    # zet de SR behoefte
    match_klas.objects.filter(pk__in=need_sr_pks).update(aantal_scheids=1)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0058_scheids_rk_bk'),
        ('Competitie', 'm0109_match_scheids'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitieindivklasse',
            name='krijgt_scheids_rk_bk',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='competitieteamklasse',
            name='krijgt_scheids_rk_bk',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(zet_scheids_rk_bk, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(zet_aantal_scheids, reverse_code=migrations.RunPython.noop),
    ]

# end of file
