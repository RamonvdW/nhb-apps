# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_locatie(apps, _):
    """ Migreer de tabellen uit Kalender naar Wedstrijden

        Maak voor elke record een nieuwe aan en verwijs van oud naar nieuw
        Relaties volgens later
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    wedstrijd_oud_klas = apps.get_model('Kalender', 'KalenderWedstrijd')

    for obj in wedstrijd_oud_klas.objects.select_related('locatie').all():      # pragma: no cover
        obj.locatie_pk = obj.locatie.pk
        obj.save(update_fields=['locatie_pk'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0023_squashed'),
        ('Kalender', 'm0012_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='locatie_pk',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(migreer_locatie),
        migrations.RemoveField(
            model_name='kalenderwedstrijd',
            name='locatie',
        ),
    ]

# end of file
