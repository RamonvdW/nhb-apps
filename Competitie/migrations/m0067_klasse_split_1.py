# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def split_klassen(apps, _):
    """ Split CompetitieKlasse op in CompetitieIndivKlasse en CompetitieTeamKlasse """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    klasse_klas = apps.get_model('Competitie', 'CompetitieKlasse')
    indiv_klas = apps.get_model('Competitie', 'CompetitieIndivKlasse')
    team_klas = apps.get_model('Competitie', 'CompetitieTeamKlasse')

    # indiv klassen
    bulk = list()
    volgorde2lkl_pks = dict()   # [volgorde] = [pk, ...]
    for klasse in (klasse_klas                                              # pragma: no cover
                   .objects
                   .exclude(indiv=None)
                   .select_related('indiv',
                                   'indiv__boogtype')
                   .prefetch_related('indiv__leeftijdsklassen')
                   .all()):

        volgorde2lkl_pks[klasse.indiv.volgorde] = list(klasse.indiv.leeftijdsklassen.values_list('pk', flat=True))

        is_18m = (klasse.competitie.afstand == '18')

        indiv = indiv_klas(
                    competitie=klasse.competitie,
                    volgorde=klasse.indiv.volgorde,
                    beschrijving=klasse.indiv.beschrijving,
                    min_ag=klasse.min_ag,
                    boogtype=klasse.indiv.boogtype,
                    is_voor_rk_bk=not klasse.indiv.niet_voor_rk_bk,
                    is_onbekend=klasse.indiv.is_onbekend,
                    is_aspirant_klasse=klasse.indiv.is_aspirant_klasse)

        if is_18m:
            indiv.blazoen1_regio = klasse.indiv.blazoen1_18m_regio
            indiv.blazoen2_regio = klasse.indiv.blazoen2_18m_regio
            indiv.blazoen_rk_bk = klasse.indiv.blazoen_18m_rk_bk
        else:
            indiv.blazoen1_regio = klasse.indiv.blazoen1_25m_regio
            indiv.blazoen2_regio = klasse.indiv.blazoen2_25m_regio
            indiv.blazoen_rk_bk = klasse.indiv.blazoen_25m_rk_bk

        bulk.append(indiv)
    # for

    indiv_klas.objects.bulk_create(bulk)

    # aanvullen met leeftijdsklassen
    for indiv in indiv_klas.objects.all():                                  # pragma: no cover
        indiv.leeftijdsklassen.set(volgorde2lkl_pks[indiv.volgorde])
    # for

    del indiv_klas
    del volgorde2lkl_pks

    # team klassen
    bulk = list()
    volgorde2boog_pks = dict()  # [volgorde] = [pk, ...]
    for klasse in (klasse_klas                                              # pragma: no cover
                   .objects
                   .exclude(team=None)
                   .select_related('team',
                                   'team__team_type')
                   .prefetch_related('team__team_type__boog_typen')
                   .all()):

        volgorde2boog_pks[klasse.team.volgorde] = \
            volgorde2boog_pks[klasse.team.volgorde + 100] = \
                list(klasse.team.team_type.boog_typen.values_list('pk', flat=True))

        is_18m = (klasse.competitie.afstand == '18')

        team = team_klas(
                competitie=klasse.competitie,
                volgorde=klasse.team.volgorde,
                beschrijving=klasse.team.beschrijving,
                team_type=klasse.team.team_type,
                team_afkorting=klasse.team.team_type.afkorting,
                min_ag=klasse.min_ag,
                is_voor_teams_rk_bk=klasse.is_voor_teams_rk_bk)

        if is_18m:
            team.blazoen1_regio = klasse.team.blazoen1_18m_regio
            team.blazoen2_regio = klasse.team.blazoen2_18m_regio
            team.blazoen_rk_bk = klasse.team.blazoen1_18m_rk_bk
        else:
            team.blazoen1_regio = klasse.team.blazoen1_25m_regio
            team.blazoen2_regio = klasse.team.blazoen2_25m_regio
            team.blazoen_rk_bk = klasse.team.blazoen_25m_rk_bk

        # geef RK/BK hogere nummers
        if team.is_voor_teams_rk_bk:
            team.volgorde += 100

        bulk.append(team)
    # for

    team_klas.objects.bulk_create(bulk)

    for team in team_klas.objects.all():                                  # pragma: no cover
        team.boog_typen.set(volgorde2boog_pks[team.volgorde])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0028_squashed'),
        ('Competitie', 'm0066_competitie_typen'),
    ]

    # migratie functies
    operations = [
        # nieuwe klassen toevoegen en kopiëren uit CompetitieKlasse
        migrations.CreateModel(
            name='CompetitieTeamKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volgorde', models.PositiveIntegerField()),
                ('beschrijving', models.CharField(max_length=80)),
                ('team_afkorting', models.CharField(max_length=3)),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
                ('is_voor_teams_rk_bk', models.BooleanField(default=False)),
                ('blazoen1_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen2_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('boog_typen', models.ManyToManyField(to='BasisTypen.BoogType')),
                ('competitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitie')),
                ('team_type', models.ForeignKey(on_delete=models.PROTECT, to='BasisTypen.TeamType')),
            ],
            options={
                'verbose_name': 'Competitie team klasse',
                'verbose_name_plural': 'Competitie team klassen',
            },
        ),
        migrations.CreateModel(
            name='CompetitieIndivKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
                ('is_onbekend', models.BooleanField(default=False)),
                ('is_aspirant_klasse', models.BooleanField(default=False)),
                ('is_voor_rk_bk', models.BooleanField(default=False)),
                ('blazoen1_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen2_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('competitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitie')),
                ('leeftijdsklassen', models.ManyToManyField(to='BasisTypen.LeeftijdsKlasse')),
            ],
            options={
                'verbose_name': 'Competitie indiv klasse',
                'verbose_name_plural': 'Competitie indiv klassen',
            },
        ),
        migrations.AddIndex(
            model_name='competitieteamklasse',
            index=models.Index(fields=['volgorde'], name='Competitie__volgord_054e8a_idx'),
        ),
        migrations.AddIndex(
            model_name='competitieindivklasse',
            index=models.Index(fields=['volgorde'], name='Competitie__volgord_476d31_idx'),
        ),
        migrations.RunPython(split_klassen),
    ]

# end of file
