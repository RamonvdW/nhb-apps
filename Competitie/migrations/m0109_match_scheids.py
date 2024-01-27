# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_match_beschrijving(apps, _):
    """ Zet de match beschrijving voor RK/BK """

    kamp_klas = apps.get_model('Competitie', 'Kampioenschap')

    for kamp in kamp_klas.objects.prefetch_related('rk_bk_matches').select_related('competitie', 'rayon').all():
        if kamp.rayon:
            msg = 'RK Rayon %s' % kamp.rayon.rayon_nr
        else:
            msg = 'BK'
        beschrijving = msg + ', ' + kamp.competitie.beschrijving
        kamp.rk_bk_matches.all().update(beschrijving=beschrijving)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0108_squashed'),
        ('Sporter', 'm0031_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(zet_match_beschrijving, reverse_code=migrations.RunPython.noop),
        migrations.AddField(
            model_name='competitiematch',
            name='aantal_scheids',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='competitiematch',
            name='gekozen_sr',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    related_name='gekozen_sr', to='Sporter.sporter'),
        ),
    ]

# end of file
