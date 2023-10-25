# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def mww_no_ver(apps, _):
    """ pas de functie van MWW aan: verwijder de koppeling met vereniging 1368 """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    functie_klas.objects.filter(rol='MWW').update(vereniging=None)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0024_geo_2'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(mww_no_ver, reverse_code=migrations.RunPython.noop)
    ]

# end of file
