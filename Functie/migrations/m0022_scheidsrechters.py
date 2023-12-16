# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def init_functies_scheidsrechters(apps, _):

    """ maak rollen aan voor de scheidsrechters """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    functie_klas(rol='CS', beschrijving='Commissie Scheidsrechters').save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0021_vereniging_2'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(init_functies_scheidsrechters, migrations.RunPython.noop),
    ]

# end of file
