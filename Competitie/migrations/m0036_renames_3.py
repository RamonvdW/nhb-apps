# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_wedstrijden(apps, _):
    """ Wedstrijd is nu CompetitieWedstrijd """

    deelnemer_klas = apps.get_model('Competitie', 'RegioCompetitieSchutterBoog')
    wedstrijd_new_klas = apps.get_model('Wedstrijden', 'CompetitieWedstrijd')

    old2new = dict()
    for wedstrijd_new in wedstrijd_new_klas.objects.prefetch_related('old').all():      # pragma: no cover
        old2new[wedstrijd_new.old.pk] = wedstrijd_new.pk
    # for

    for deelnemer in deelnemer_klas.objects.prefetch_related('inschrijf_gekozen_wedstrijden').all():    # pragma: no cover
        wedstrijden = list()
        for wedstrijd_pk in deelnemer.inschrijf_gekozen_wedstrijden.values_list('pk', flat=True):
            wedstrijden.append(old2new[wedstrijd_pk])
        # for

        deelnemer.inschrijf_gekozen_wedstrijden2.set(wedstrijden)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0035_verwijder_oude_ag_velden'),
        ('Wedstrijden', 'm0012_renames_3'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_gekozen_wedstrijden2',
            field=models.ManyToManyField(blank=True, to='Wedstrijden.CompetitieWedstrijd'),
        ),
        migrations.RunPython(migreer_wedstrijden)
    ]

# end of file
