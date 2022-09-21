# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.models import ORGANISATIE_IFAA


def update_ifaa_leeftijdsklassen(apps, _):
    """ Verwijder de leeftijdsgrenzen van de IFAA Volwassenen klassen (M/V)
        zodat dit de "open klasse" wordt.
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    # 41 = Volwassen Dames, IFAA
    # 42 = Volwassen Heren, IFAA

    for volgorde in (41, 42):
        lkl = leeftijdsklasse_klas.objects.get(volgorde=volgorde, organisatie=ORGANISATIE_IFAA)
        lkl.min_wedstrijdleeftijd = 0
        lkl.max_wedstrijdleeftijd = 0
        lkl.save(update_fields=['min_wedstrijdleeftijd', 'max_wedstrijdleeftijd'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0046_wkl_refresh')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(update_ifaa_leeftijdsklassen),
    ]

# end of file
