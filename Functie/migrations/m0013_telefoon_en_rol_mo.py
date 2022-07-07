# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def maak_rol_mo(apps, _):
    """ nieuwe rol voor de Manager Opleidingen """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    functie_klas(beschrijving='Manager opleidingen', rol='MO').save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0012_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='functie',
            name='telefoon',
            field=models.CharField(blank=True, default='', max_length=25),
        ),
        migrations.RunPython(maak_rol_mo),
    ]

# end of file
