# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_regio(apps, _):
    teamrk_klas = apps.get_model('CompLaagRayon', 'TeamRK')
    regiodeelnemer_klas = apps.get_model('CompLaagRegio', 'RegioDeelnemer')

    sporterboog_pk_afstand2regiodeelnemer = dict()
    for deelnemer in regiodeelnemer_klas.objects.select_related('sporterboog', 'regiocomp__competitie').all():
        sporterboog_pk = deelnemer.sporterboog.pk
        afstand = deelnemer.regiocomp.competitie.afstand
        tup = (sporterboog_pk, afstand)
        sporterboog_pk_afstand2regiodeelnemer[tup] = deelnemer
    # for

    for teamrk in teamrk_klas.objects.prefetch_related('tijdelijke_leden').all():

        nieuwe_deelnemers = list()
        for rcsb in teamrk.tijdelijke_leden.select_related('sporterboog', 'regiocompetitie__competitie').all():
            sporterboog_pk = rcsb.sporterboog.pk
            afstand = rcsb.regiocompetitie.competitie.afstand
            tup = (sporterboog_pk, afstand)
            deelnemer = sporterboog_pk_afstand2regiodeelnemer[tup]
            nieuwe_deelnemers.append(deelnemer)
        # for

        teamrk.tijdelijke_deelnemers_regio.set(nieuwe_deelnemers)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('CompLaagRayon', 'm0003_logboek'),
        ('CompLaagRegio', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='teamrk',
            name='tijdelijke_deelnemers_regio',
            field=models.ManyToManyField(blank=True, related_name='teamrk_tijdelijk', to='CompLaagRegio.regiodeelnemer'),
        ),
        migrations.RunPython(migreer_regio, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='teamrk',
            name='tijdelijke_leden',
        ),
    ]

# end of file
