# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def migrate_sporterboog(apps, _):
    """ Voorzie elke Score van sporterboog naast schutterboog """

    # haal de klassen op
    deelnemer_klas = apps.get_model('Competitie', 'RegioCompetitieSchutterBoog')
    kampioen_klas = apps.get_model('Competitie', 'KampioenschapSchutterBoog')
    sporterboog_klas = apps.get_model('Sporter', 'SporterBoog')

    # maak een cache
    cache = dict()      # [sporter.lid_nr] = SporterBoog
    for sporterboog in (sporterboog_klas
                        .objects
                        .select_related('sporter',
                                        'boogtype')
                        .all()):                            # pragma: no cover

        tup = (sporterboog.sporter.lid_nr, sporterboog.boogtype.afkorting)
        cache[tup] = sporterboog
    # for

    # voorzie elke deelnemer van sporterboog
    for obj in (deelnemer_klas
                .objects
                .select_related('schutterboog__nhblid',
                                'schutterboog__boogtype')
                .all()):                                    # pragma: no cover

        tup = (obj.schutterboog.nhblid.nhb_nr, obj.schutterboog.boogtype.afkorting)
        obj.sporterboog = cache[tup]
        obj.save(update_fields=['sporterboog'])
    # for

    # voorzie elke kampioen van sporterboog
    for obj in (kampioen_klas
                .objects
                .select_related('schutterboog__nhblid')
                .all()):                                    # pragma: no cover

        tup = (obj.schutterboog.nhblid.nhb_nr, obj.schutterboog.boogtype.afkorting)
        obj.sporterboog = cache[tup]
        obj.save(update_fields=['sporterboog'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0002_copy_data'),
        ('Competitie', 'm0053_teams_rk'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapschutterboog',
            name='sporterboog',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='Sporter.sporterboog'),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='sporterboog',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='Sporter.sporterboog'),
        ),
        migrations.RunPython(migrate_sporterboog),
        migrations.RemoveField(
            model_name='kampioenschapschutterboog',
            name='schutterboog'),
        migrations.RemoveField(
            model_name='regiocompetitieschutterboog',
            name='schutterboog'),
    ]

# end of file
