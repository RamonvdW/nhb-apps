# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def corrigeer_ifaa_beschrijving(apps, _):
    """ Corrigeer de beschrijving van de IFAA welp klassen

        Welpen jongen --> Welpen jongens
    """

    ifaa = 'F'  # International Field Archery Association

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    # deel 1
    for klasse in kalenderwedstrijdklasse_klas.objects.filter(organisatie=ifaa):        # pragma: no cover
        if klasse.beschrijving.endswith('Welpen jongen'):
            klasse.beschrijving += 's'
            klasse.save(update_fields=['beschrijving'])
    # for

    # deel 2
    for klasse in leeftijdsklasse_klas.objects.filter(organisatie=ifaa):                # pragma: no cover
        if klasse.beschrijving.endswith('Welpen jongen'):
            klasse.beschrijving += 's'
            klasse.save(update_fields=['beschrijving'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0042_squashed')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(corrigeer_ifaa_beschrijving),
    ]

# end of file
