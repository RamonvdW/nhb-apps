# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def maak_functie_mla(apps, _):
    """ maak rol aan voor de Manager Ledenadministratie """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    functie_klas(rol='MLA', beschrijving='Manager Ledenadministratie').save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0025_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(maak_functie_mla),
    ]

# end of file
