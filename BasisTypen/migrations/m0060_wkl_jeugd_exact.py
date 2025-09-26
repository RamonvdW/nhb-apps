# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.definities import ORGANISATIE_WA_STRIKT, GESLACHT_MAN, GESLACHT_VROUW


LEEFTIJDSKLASSEN_STRIKT = (
    # WA
    # volgorde afk     geslacht        min max  kort         beschrijving                organisatie

    # 18 t/m 20 jaar
    (35,       'JVS',  GESLACHT_VROUW, 18, 20,  'Onder 21', 'Onder 21 Dames (strikt)',   ORGANISATIE_WA_STRIKT),
    (36,       'JHS',  GESLACHT_MAN,   18, 20,  'Onder 21', 'Onder 21 Heren (strikt)',   ORGANISATIE_WA_STRIKT),

    # 14 t/m 17 jaar
    (25,       'CVS',  GESLACHT_VROUW, 14, 17,  'Onder 18', 'Onder 18 Dames (strikt)',   ORGANISATIE_WA_STRIKT),
    (26,       'CHS',  GESLACHT_MAN,   14, 17,  'Onder 18', 'Onder 18 Heren (strikt)',   ORGANISATIE_WA_STRIKT),

    # 12 t/m 13 jaar
    (18,       'AV2S', GESLACHT_VROUW, 12, 13,  'Onder 14', 'Onder 14 Meisjes (strikt)', ORGANISATIE_WA_STRIKT),
    (19,       'AH2S', GESLACHT_MAN,   12, 13,  'Onder 14', 'Onder 14 Jongens (strikt)', ORGANISATIE_WA_STRIKT),
)


KALENDERWEDSTRIJDENKLASSEN_STRIKT = (
    # nr  boog  lkl    afk       beschrijving
    (136, 'R',  'JVS',  'R1820D', 'Recurve Onder 21 Dames (strikt)'),
    (137, 'R',  'JHS',  'R1820H', 'Recurve Onder 21 Heren (strikt)'),

    (146, 'R',  'CVS',  'R1417D', 'Recurve Onder 18 Dames (strikt)'),
    (147, 'R',  'CHS',  'R1417H', 'Recurve Onder 18 Heren (strikt)'),

    (156, 'R',  'AH2S', 'R1213H', 'Recurve Onder 14 Jongens (strikt)'),
    (157, 'R',  'AV2S', 'R1213D', 'Recurve Onder 14 Meisjes (strikt)'),

    (236, 'C',  'JVS',  'C1820D', 'Compound Onder 21 jaar Dames (strikt)'),
    (237, 'C',  'JHS',  'C1820H', 'Compound Onder 21 jaar Heren (strikt)'),

    (246, 'C',  'CVS',  'C1417D', 'Compound Onder 18 jaar Dames (strikt)'),
    (247, 'C',  'CHS',  'C1417H', 'Compound Onder 18 jaar Heren (strikt)'),

    (256, 'C',  'AH2S', 'C1213H', 'Compound Onder 14 Jongens (strikt)'),
    (257, 'C',  'AV2S', 'C1213D', 'Compound Onder 14 Meisjes (strikt)'),

    (336, 'BB', 'JVS',  'B1820D', 'Barebow Onder 21 jaar Dames (strikt)'),
    (337, 'BB', 'JHS',  'B1820H', 'Barebow Onder 21 jaar Heren (strikt)'),

    (346, 'BB', 'CVS',  'B1417D', 'Barebow Onder 18 jaar Dames (strikt)'),
    (347, 'BB', 'CHS',  'B1417H', 'Barebow Onder 18 jaar Heren (strikt)'),

    (356, 'BB', 'AH2S', 'B1213H', 'Barebow Onder 14 Jongens (strikt)'),
    (357, 'BB', 'AV2S', 'B1213D', 'Barebow Onder 14 Meisjes (strikt)'),
)


def init_leeftijdsklassen_exact(apps, _):
    """ Maak de extra leeftijdsklassen aan """

    # leeftijdsklassen volgens spec v2.1, deel 3, tabel 3.1

    # note: wedstrijdleeftijd = leeftijd die je bereikt in een jaar
    #       competitieleeftijd = wedstrijdleeftijd + 1

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    bulk = list()
    for volgorde, afkorting, geslacht, leeftijd_min, leeftijd_max, kort, beschrijving, organisatie in LEEFTIJDSKLASSEN_STRIKT:
        lkl = leeftijdsklasse_klas(
                    afkorting=afkorting,
                    wedstrijd_geslacht=geslacht,
                    klasse_kort=kort,
                    beschrijving=beschrijving,
                    volgorde=volgorde,
                    min_wedstrijdleeftijd=leeftijd_min,
                    max_wedstrijdleeftijd=leeftijd_max,
                    organisatie=organisatie)

        bulk.append(lkl)
    # for

    leeftijdsklasse_klas.objects.bulk_create(bulk)


def init_kalenderwedstrijdklassen_exact(apps, _):
    """ Maak de extra kalender wedstrijdklassen aan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    afk2boog = dict()       # [afkorting] = BoogType
    for boog in boogtype_klas.objects.all():
        afk2boog[boog.afkorting] = boog
    # for

    afk2lkl = dict()        # [afkorting] = Leeftijdsklasse
    for lkl in leeftijdsklasse_klas.objects.all():
        afk2lkl[lkl.afkorting] = lkl
    # for

    bulk = list()
    for volgorde, boog_afk, lkl_afk, afkorting, beschrijving in KALENDERWEDSTRIJDENKLASSEN_STRIKT:
        boog = afk2boog[boog_afk]
        lkl = afk2lkl[lkl_afk]

        obj = kalenderwedstrijdklasse_klas(
                        beschrijving=beschrijving,
                        boogtype=boog,
                        leeftijdsklasse=lkl,
                        volgorde=volgorde,
                        afkorting=afkorting,
                        organisatie=lkl.organisatie)
        bulk.append(obj)
    # for
    kalenderwedstrijdklasse_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0059_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(init_leeftijdsklassen_exact, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(init_kalenderwedstrijdklassen_exact, reverse_code=migrations.RunPython.noop),
    ]

# end of file
