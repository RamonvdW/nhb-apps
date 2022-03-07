# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def migreer_matches(apps, _):

    wedstrijd_klas = apps.get_model('Wedstrijden', 'CompetitieWedstrijd')
    match_klas = apps.get_model('Competitie', 'CompetitieMatch')

    deelnemer_klas = apps.get_model('Competitie', 'RegioCompetitieSchutterBoog')
    deelcomp_klas = apps.get_model('Competitie', 'DeelCompetitie')
    ronde_klas = apps.get_model('Competitie', 'DeelcompetitieRonde')

    indiv_klas = apps.get_model('Competitie', 'CompetitieIndivKlasse')
    team_klas = apps.get_model('Competitie', 'CompetitieTeamKlasse')

    comp_volgorde2indiv_pk = dict()    # [(comp.pk, volgorde)] = CompetitieIndivKlasse
    comp_volgorde2team_pk = dict()     # [(comp.pk, volgorde)] = CompetitieTeamKlasse
    wedstrijd_pk2match_pk = dict()     # [CompetitieWedstrijd.pk] = CompetitieMatch.pk

    for indiv in indiv_klas.objects.prefetch_related('competitie'):
        tup = (indiv.competitie.pk, indiv.volgorde)
        comp_volgorde2indiv_pk[tup] = indiv.pk
    # for

    for team in team_klas.objects.prefetch_related('competitie'):
        tup = (team.competitie.pk, team.volgorde)
        comp_volgorde2team_pk[tup] = team.pk
    # for

    # migreer DeelcompetitieRonde
    for ronde in (ronde_klas
                  .objects
                  .exclude(plan=None)
                  .select_related('plan',
                                  'deelcompetitie',
                                  'deelcompetitie__competitie')
                  .prefetch_related('plan__wedstrijden')
                  .all()):

        comp = ronde.deelcompetitie.competitie

        # vertaal plan.wedstrijden naar nieuwe matches

        matches = list()
        for wedstrijd in ronde.plan.wedstrijden.all():
            match = match_klas(
                        competitie=comp,
                        beschrijving=wedstrijd.beschrijving,
                        vereniging=wedstrijd.vereniging,
                        locatie=wedstrijd.locatie,
                        datum_wanneer=wedstrijd.datum_wanneer,
                        tijd_begin_wedstrijd=wedstrijd.tijd_begin_wedstrijd)

            if wedstrijd.uitslag:
                match.uitslag = wedstrijd.uitslag.nieuwe_uitslag

            match.save()
            matches.append(match)

            wedstrijd_pk2match_pk[wedstrijd.pk] = match.pk

            # vertaal de oude indiv/team_klassen naar de nieuwe CompetitieIndiv/TeamKlasse

            pks = list()
            for indiv_old in wedstrijd.indiv_klassen.all():
                tup = (comp.pk, indiv_old.volgorde)
                pks.append(comp_volgorde2indiv_pk[tup])
            # for
            match.indiv_klassen.set(pks)

            pks = list()
            for team_old in wedstrijd.team_klassen.all():
                tup = (comp.pk, team_old.volgorde)
                pks.append(comp_volgorde2team_pk[tup])
            # for
            match.team_klassen.set(pks)
        # for

        ronde.matches.set(matches)
    # for

    # migreer de RK/BK deelcompetities
    for deelcomp in (deelcomp_klas
                     .objects
                     .exclude(plan=None)
                     .select_related('competitie',
                                     'plan')):

        comp = deelcomp.competitie

        matches = list()
        for wedstrijd in deelcomp.plan.wedstrijden.all():

            match = match_klas(
                        competitie=comp,
                        beschrijving=wedstrijd.beschrijving,
                        vereniging=wedstrijd.vereniging,
                        locatie=wedstrijd.locatie,
                        datum_wanneer=wedstrijd.datum_wanneer,
                        tijd_begin_wedstrijd=wedstrijd.tijd_begin_wedstrijd)

            if wedstrijd.uitslag:
                match.uitslag = wedstrijd.uitslag.nieuwe_uitslag

            match.save()
            matches.append(match)

            # vertaal de oude indiv/team_klassen naar de nieuwe CompetitieIndiv/TeamKlasse

            pks = list()
            for indiv_old in wedstrijd.indiv_klassen.all():
                tup = (comp.pk, indiv_old.volgorde)
                pks.append(comp_volgorde2indiv_pk[tup])
            # for
            match.indiv_klassen.set(pks)

            pks = list()
            for team_old in wedstrijd.team_klassen.all():
                tup = (comp.pk, team_old.volgorde)
                pks.append(comp_volgorde2team_pk[tup])
            # for
            match.team_klassen.set(pks)
        # for

        deelcomp.rk_bk_matches.set(matches)
    # for

    # migreer gekozen wedstrijden inschrijfmethode 1
    for deelnemer in (deelnemer_klas
                      .objects
                      .prefetch_related('inschrijf_gekozen_wedstrijden')):

        pks = list()
        for pk in deelnemer.inschrijf_gekozen_wedstrijden.values_list('pk', flat=True):
            pks.append(wedstrijd_pk2match_pk[pk])
        # for
        deelnemer.inschrijf_gekozen_matches.set(pks)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0070_klasse_split_4'),
        ('NhbStructuur', 'm0024_squashed'),
        ('Score', 'm0016_uitslag_2'),
        ('Wedstrijden', 'm0021_nieuwe_uitslag'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='CompetitieMatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('competitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitie')),
                ('beschrijving', models.CharField(blank=True, max_length=100)),
                ('datum_wanneer', models.DateField()),
                ('tijd_begin_wedstrijd', models.TimeField()),
                ('indiv_klassen', models.ManyToManyField(blank=True, to='Competitie.CompetitieIndivKlasse')),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.wedstrijdlocatie')),
                ('team_klassen', models.ManyToManyField(blank=True, to='Competitie.CompetitieTeamKlasse')),
                ('uitslag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Score.uitslag')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
            ],
            options={
                'verbose_name': 'Competitie Match',
                'verbose_name_plural': 'Competitie Matches',
            },
        ),
        migrations.AddField(
            model_name='deelcompetitie',
            name='rk_bk_matches',
            field=models.ManyToManyField(blank=True, to='Competitie.CompetitieMatch'),
        ),
        migrations.AddField(
            model_name='deelcompetitieronde',
            name='matches',
            field=models.ManyToManyField(blank=True, to='Competitie.CompetitieMatch'),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_gekozen_matches',
            field=models.ManyToManyField(blank=True, to='Competitie.CompetitieMatch'),
        ),
        migrations.RunPython(migreer_matches)
    ]

# end of file
