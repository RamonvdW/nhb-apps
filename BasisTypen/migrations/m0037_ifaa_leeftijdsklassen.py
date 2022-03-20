# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.models import GESLACHT_ALLE, GESLACHT_VROUW, GESLACHT_MAN


def maak_leeftijdsklassen_ifaa(apps, _):
    """ Voeg de leeftijdsklassen voor IFAA toe.
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    ifaa = 'F'  # International Field Archery Association

    bulk = [
        # Senioren / 65+
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='SEM',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Sen M',
            beschrijving='Senioren mannen (65+)',
            volgorde=62,
            min_wedstrijdleeftijd=65,
            max_wedstrijdleeftijd=0),
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='SEV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Sen V',
            beschrijving='Senioren vrouwen (65+)',
            volgorde=61,
            min_wedstrijdleeftijd=65,
            max_wedstrijdleeftijd=0),

        # Veteranen / 55-64
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='VEM',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Vet',
            beschrijving='Veteranen mannen (55+)',
            volgorde=52,
            min_wedstrijdleeftijd=55,
            max_wedstrijdleeftijd=0),
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='VEV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Vet V',
            beschrijving='Veteranen vrouwen (55+)',
            volgorde=51,
            min_wedstrijdleeftijd=55,
            max_wedstrijdleeftijd=0),

        # Volwassenen (21-54)
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='VWH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Volw M',
            beschrijving='Volwassenen mannen',
            volgorde=42,
            min_wedstrijdleeftijd=21,
            max_wedstrijdleeftijd=54),

        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='VWV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Volw V',
            beschrijving='Volwassenen vrouwen',
            volgorde=41,
            min_wedstrijdleeftijd=21,
            max_wedstrijdleeftijd=54),

        # Jong volwassenen (17-20)
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='JVH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Jong M',
            beschrijving='Jong volwassenen mannen',
            volgorde=32,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20),

        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='JVV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Jong V',
            beschrijving='Jong volwassenen vrouwen',
            volgorde=31,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20),

        # Junioren (13-16)
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='JUH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Jun M',
            beschrijving='Junioren jongens',
            volgorde=22,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=16),

        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='JUV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Jun V',
            beschrijving='Junioren meisjes',
            volgorde=21,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=16),

        # Welpen (<13)
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='WEH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Welp M',
            beschrijving='Welpen jongen',
            volgorde=12,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=12),

        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='WEV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Welp V',
            beschrijving='Welpen meisjes',
            volgorde=11,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=12),
    ]

    leeftijdsklasse_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0036_corrigeer_kalender_140'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(maak_leeftijdsklassen_ifaa),
    ]

# end of file
