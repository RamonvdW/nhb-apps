# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.models import ORGANISATIE_IFAA


def corrigeer_ifaa_volwassenen(apps, _):
    """ Corrigeer slecht nederlands in de beschrijving van de IFAA leeftijdsklassen en wedstrijdklassen """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kwk_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    for klasse in kwk_klas.objects.all():                                       # pragma: no cover
        pos = klasse.beschrijving.find('Jong volwassenen ')
        if pos >= 0:
            klasse.beschrijving = klasse.beschrijving[:pos] + 'Jongvolwassen ' + klasse.beschrijving[pos+17:]
            klasse.save(update_fields=['beschrijving'])

        pos = klasse.beschrijving.find('Volwassenen ')
        if pos >= 0:
            klasse.beschrijving = klasse.beschrijving[:pos] + 'Volwassen ' + klasse.beschrijving[pos+12:]
            klasse.save(update_fields=['beschrijving'])
    # for

    for klasse in lkl_klas.objects.filter(organisatie=ORGANISATIE_IFAA):        # pragma: no cover
        pos = klasse.beschrijving.find('Jong volwassenen ')
        if pos >= 0:
            klasse.beschrijving = klasse.beschrijving[:pos] + 'Jongvolwassen ' + klasse.beschrijving[pos+17:]
            klasse.save(update_fields=['beschrijving'])

        pos = klasse.beschrijving.find('Volwassenen ')
        if pos >= 0:
            klasse.beschrijving = klasse.beschrijving[:pos] + 'Volwassen ' + klasse.beschrijving[pos+12:]
            klasse.save(update_fields=['beschrijving'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0040_nhb_onder12'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(corrigeer_ifaa_volwassenen),
    ]

# end of file
