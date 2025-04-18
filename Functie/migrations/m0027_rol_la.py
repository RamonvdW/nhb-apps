# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def maak_functie_la(apps, _):
    """ maak rol aan voor de Manager Ledenadministratie """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')
    ver_klas = apps.get_model('Vereniging', 'Vereniging')

    bulk = list()
    for ver in ver_klas.objects.all():
        bulk.append(
            functie_klas(
                rol='LA',
                beschrijving='Ledenadministratie %s' % ver.ver_nr,
                vereniging=ver)
        )
    # for

    functie_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0026_rol_mla'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(maak_functie_la),
    ]

# end of file
