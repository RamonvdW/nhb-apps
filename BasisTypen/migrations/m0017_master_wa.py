# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def corrigeer_leeftijdsklassen(apps, _):
    """ Maak de Masters leeftijdsklassen WA-approved, dus beschikbaar in A-status wedstrijd """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    # pas de senioren klassen aan
    for lkl in leeftijdsklasse_klas.objects.filter(klasse_kort='Master'):       # pragma: no cover
        lkl.volgens_wa = True
        lkl.save(update_fields=['volgens_wa'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0016_leeftijdsklasse_volgorde'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(corrigeer_leeftijdsklassen),
    ]

# end of file
