# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.migrations.m0042_squashed import LEEFTIJDSKLASSEN


def update_leeftijdsklassen(apps, _):
    """ Verversen / corrigeren van de beschrijvingen van de leeftijdsklassen
        inclusief het verwijderen van de oude WA namen
        en een paar kleine foutjes
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    org_volg2lkl = dict()       # [(organisatie, volgorde)] = Leeftijdsklasse()
    for lkl in leeftijdsklasse_klas.objects.all():
        org_volg2lkl[(lkl.organisatie, lkl.volgorde)] = lkl
    # for

    for volgorde, afkorting, geslacht, leeftijd_min, leeftijd_max, kort, beschrijving, organisatie in LEEFTIJDSKLASSEN:
        tup = (organisatie, volgorde)
        lkl = org_volg2lkl[tup]
        del org_volg2lkl[tup]

        assert lkl.afkorting == afkorting
        assert lkl.wedstrijd_geslacht == geslacht
        assert lkl.min_wedstrijdleeftijd == leeftijd_min
        assert lkl.max_wedstrijdleeftijd == leeftijd_max

        if lkl.klasse_kort != kort:                 # pragma: no cover
            lkl.klasse_kort = kort
            lkl.save(update_fields=['klasse_kort'])

        if lkl.beschrijving != beschrijving:        # pragma: no cover
            lkl.beschrijving = beschrijving
            lkl.save(update_fields=['beschrijving'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0045_wkl_afk_beschr')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(update_leeftijdsklassen),
    ]

# end of file
