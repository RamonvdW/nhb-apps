# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def hernoem_gebruikte_functie(apps, _):
    """ Hernoem de gebruikte functie """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    regel_klas = apps.get_model('Logboek', 'LogboekRegel')

    (regel_klas
     .objects
     .filter(gebruikte_functie='Registreer met NHB nummer')
     .update(gebruikte_functie='Registreer normaal'))

    (regel_klas
     .objects
     .filter(gebruikte_functie='Registreer met bondsnummer')
     .update(gebruikte_functie='Registreer normaal'))


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Logboek', 'm0002_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(hernoem_gebruikte_functie, migrations.RunPython.noop)
    ]

# end of file
