# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


ADMINISTRATIEVE_REGIO = 100
VER_NR = 1368


def maak_rol_mww(apps, _):

    """ Maak de nieuwe rol Manager Webwinkel (MWW) aan """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')
    ver_klas = apps.get_model('NhbStructuur', 'NhbVereniging')

    ver = ver_klas.objects.get(ver_nr=VER_NR)

    functie_klas(
        rol='MWW',
        beschrijving='Manager Webwinkel',
        nhb_ver=ver).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0015_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(maak_rol_mww, reverse_code=migrations.RunPython.noop),
    ]

# end of file
