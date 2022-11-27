# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations

ADMINISTRATIEVE_REGIO = 100
VER_NR = 1368


def maak_ver_bondsbureau(apps, _):

    """ Maak de vereniging Bondsbureau aan, want deze is nodig voor de functie MWW
        Verdere details volgen uit de CRM import.
    """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    ver_klas = apps.get_model('NhbStructuur', 'NhbVereniging')

    # alleen bij een lege database aanmaken
    ver, is_created = ver_klas.objects.get_or_create(
                                    ver_nr=VER_NR,
                                    regio=regio_klas.objects.get(regio_nr=ADMINISTRATIEVE_REGIO))
    if is_created:      # pragma: branch
        ver.naam = 'Tijdelijk'
        ver.save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0029_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(maak_ver_bondsbureau, reverse_code=migrations.RunPython.noop),
    ]

# end of file
