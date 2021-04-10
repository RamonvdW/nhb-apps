# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def copy_wedstrijden(apps, _):
    """ kopieer Wedstrijd naar CompetitieWedstrijd """

    wedstrijd_old_klas = apps.get_model('Wedstrijden', 'Wedstrijd')
    wedstrijd_new_klas = apps.get_model('Wedstrijden', 'CompetitieWedstrijd')

    bulk = list()
    for wedstrijd_old in wedstrijd_old_klas.objects.all():      # pragma: no cover
        wedstrijd_new = wedstrijd_new_klas(
                            beschrijving=wedstrijd_old.beschrijving,
                            preliminair=wedstrijd_old.preliminair,
                            vereniging=wedstrijd_old.vereniging,
                            locatie=wedstrijd_old.locatie,
                            datum_wanneer=wedstrijd_old.datum_wanneer,
                            tijd_begin_aanmelden=wedstrijd_old.tijd_begin_aanmelden,
                            tijd_begin_wedstrijd=wedstrijd_old.tijd_begin_wedstrijd,
                            tijd_einde_wedstrijd=wedstrijd_old.tijd_einde_wedstrijd,
                            uitslag=wedstrijd_old.uitslag,
                            old=wedstrijd_old)

        bulk.append(wedstrijd_new)
        if len(bulk) > 500:
            wedstrijd_new_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):
        wedstrijd_new_klas.objects.bulk_create(bulk)

    for wedstrijd_new in (wedstrijd_new_klas
                          .objects
                          .select_related('old')
                          .prefetch_related('indiv_klassen',
                                            'team_klassen')
                          .all()):                        # pragma: no cover

        wedstrijd_old = wedstrijd_new.old
        wedstrijd_new.indiv_klassen.set(wedstrijd_old.indiv_klassen.all())
        wedstrijd_new.team_klassen.set(wedstrijd_old.team_klassen.all())

        for plan in wedstrijd_old.wedstrijdenplan_set.all():
            plan.wedstrijd2 = wedstrijd_new
            plan.save()
        # for
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0017_rename_ver_nhb_nr'),
        ('BasisTypen', 'm0014_remove_team_wkl_boogtypen'),
        ('Wedstrijden', 'm0011_discipline_25m1pijl'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='CompetitieWedstrijd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(blank=True, max_length=100)),
                ('preliminair', models.BooleanField(default=True)),
                ('datum_wanneer', models.DateField()),
                ('tijd_begin_aanmelden', models.TimeField()),
                ('tijd_begin_wedstrijd', models.TimeField()),
                ('tijd_einde_wedstrijd', models.TimeField()),
                ('indiv_klassen', models.ManyToManyField(blank=True, to='BasisTypen.IndivWedstrijdklasse')),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijdlocatie')),
                ('team_klassen', models.ManyToManyField(blank=True, to='BasisTypen.TeamWedstrijdklasse')),
                ('uitslag', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Wedstrijden.competitiewedstrijduitslag')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('old', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Wedstrijden.wedstrijd')),
            ],
            options={
                'verbose_name': 'Competitie Wedstrijd',
                'verbose_name_plural': 'Competitie Wedstrijden',
            },
        ),
        migrations.AddField(
            model_name='wedstrijdenplan',
            name='wedstrijden2',
            field=models.ManyToManyField(blank=True, related_name='wedstrijdenplan2', to='Wedstrijden.CompetitieWedstrijd'),
        ),
        migrations.RunPython(copy_wedstrijden)
    ]

# end of file
