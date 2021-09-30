# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migrate_sporterboog(apps, _):
    """ Voorzie elke Score van sporterboog naast schutterboog """

    # haal de klassen op
    sessie_klas = apps.get_model('Kalender', 'KalenderWedstrijdSessie')
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

    # vertaal KalenderWedstrijdSessie.aanmeldingen naar sporters
    for sessie in (sessie_klas
                   .objects
                   .prefetch_related('aanmeldingen')
                   .all()):                                 # pragma: no cover

        sporters = list()
        for obj in (sessie
                    .aanmeldingen
                    .select_related('nhblid',
                                    'boogtype')
                    .all()):

            tup = (obj.nhblid.nhb_nr, obj.boogtype.afkorting)
            sporterboog = cache[tup]
            sporters.append(sporterboog)
        # for

        sessie.sporters.set(sporters)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0002_copy_data'),
        ('Kalender', 'm0004_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalenderwedstrijdsessie',
            name='sporters',
            field=models.ManyToManyField(blank=True, to='Sporter.SporterBoog'),
        ),
        migrations.RunPython(migrate_sporterboog),
        migrations.RemoveField(
            model_name='kalenderwedstrijdsessie',
            name='aanmeldingen',
        ),
    ]

# end of file
