# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def migreer_klassen(apps, _):
    """ Zet elke ForeignKey die verwijst naar een CompetitieKlasse om
        in een CompetitieIndivKlasse of CompetitieTeamKlasse
    """

    team_klas = apps.get_model('Competitie', 'CompetitieTeamKlasse')
    indiv_klas = apps.get_model('Competitie', 'CompetitieIndivKlasse')
    klasse_klas = apps.get_model('Competitie', 'CompetitieKlasse')

    # maak een vertaal tabel
    comp_volgorde2team = dict()      # [(comp.pk, volgorde)] = CompetitieTeamKlasse
    comp_volgorde2indiv = dict()     # [(comp.pk, volgorde)] = CompetitieIndivKlasse

    if True:
        for indiv in indiv_klas.objects.all():                      # pragma: no cover
            tup = (indiv.competitie.pk, indiv.volgorde)
            comp_volgorde2indiv[tup] = indiv
        # for

        for team in team_klas.objects.all():                        # pragma: no cover
            tup = (team.competitie.pk, team.volgorde)
            comp_volgorde2team[tup] = team
        # for

    klasse_pk2team = dict()     # [klasse.pk] = CompetitieTeamKlasse
    klasse_pk2indiv = dict()    # [klasse.pk] = CompetitieIndivKlasse
    if True:
        for klasse in klasse_klas.objects.select_related('competitie', 'indiv', 'team').all():      # pragma: no cover
            if klasse.team:
                volgorde = klasse.team.volgorde
                if klasse.is_voor_teams_rk_bk:
                    volgorde += 100
                tup = (klasse.competitie.pk, volgorde)
                klasse_pk2team[klasse.pk] = comp_volgorde2team[tup]
            else:
                tup = (klasse.competitie.pk, klasse.indiv.volgorde)
                klasse_pk2indiv[klasse.pk] = comp_volgorde2indiv[tup]
        # for

    # CompetitieMutatie
    if True:
        mutatie_klas = apps.get_model('Competitie', 'CompetitieMutatie')

        for mutatie in mutatie_klas.objects.exclude(klasse=None).select_related('klasse').all():    # pragma: no cover
            if mutatie.klasse:
                try:
                    mutatie.indiv_klasse = klasse_pk2indiv[mutatie.klasse.pk]
                except KeyError:
                    pass
                else:
                    mutatie.save(update_fields=['indiv_klasse'])

                try:
                    mutatie.team_klasse = klasse_pk2team[mutatie.klasse.pk]
                except KeyError:
                    pass
                else:
                    mutatie.save(update_fields=['team_klasse'])
        # for

    # DeelCompetitieKlasseLimiet
    if True:
        limiet_klas = apps.get_model('Competitie', 'DeelCompetitieKlasseLimiet')

        for limiet in limiet_klas.objects.select_related('klasse').all():                           # pragma: no cover
            if limiet.klasse:
                try:
                    limiet.indiv_klasse = klasse_pk2indiv[limiet.klasse.pk]
                except KeyError:
                    pass
                else:
                    limiet.save(update_fields=['indiv_klasse'])

                try:
                    limiet.team_klasse = klasse_pk2team[limiet.klasse.pk]
                except KeyError:
                    pass
                else:
                    limiet.save(update_fields=['team_klasse'])
        # for

    # RegioCompetitieSchutterBoog
    if True:
        deelnemer_klas = apps.get_model('Competitie', 'RegioCompetitieSchutterBoog')

        for deelnemer in deelnemer_klas.objects.select_related('klasse').all():                     # pragma: no cover
            deelnemer.indiv_klasse = klasse_pk2indiv[deelnemer.klasse.pk]
            deelnemer.save(update_fields=['indiv_klasse'])
        # for

    # KampioenschapSchutterBoog
    if True:
        kampioen_klas = apps.get_model('Competitie', 'KampioenschapSchutterBoog')

        for kampioen in kampioen_klas.objects.select_related('klasse').all():                       # pragma: no cover
            kampioen.indiv_klasse = klasse_pk2indiv[kampioen.klasse.pk]
            kampioen.save(update_fields=['indiv_klasse'])
        # for

    # RegioCompetitieTeam
    if True:
        regioteam_klas = apps.get_model('Competitie', 'RegioCompetitieTeam')

        for regioteam in regioteam_klas.objects.select_related('klasse').all():                     # pragma: no cover
            regioteam.team_klasse = klasse_pk2team[regioteam.klasse.pk]
            regioteam.save(update_fields=['team_klasse'])
        # for

    # KampioenschapTeam
    if True:
        kampteam_klas = apps.get_model('Competitie', 'KampioenschapTeam')

        for kampteam in kampteam_klas.objects.select_related('klasse').all():                       # pragma: no cover
            if kampteam.klasse:
                kampteam.team_klasse = klasse_pk2team[kampteam.klasse.pk]
                kampteam.save(update_fields=['team_klasse'])
        # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0068_klasse_split_2'),
    ]

    # migratie functies
    operations = [
        # gebruik van CompetitieKlasse migreren naar de nieuwe klassen
        migrations.RunPython(migreer_klassen),

        # enforce key presence
        migrations.AlterField(
            model_name='kampioenschapschutterboog',
            name='indiv_klasse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieindivklasse'),
        ),
        migrations.AlterField(
            model_name='regiocompetitieschutterboog',
            name='indiv_klasse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieindivklasse'),
        ),
    ]

# end of file
