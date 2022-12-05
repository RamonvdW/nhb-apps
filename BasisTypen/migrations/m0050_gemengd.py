# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.models import (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_60CM, BLAZOEN_60CM_4SPOT,
                               ORGANISATIE_WA, ORGANISATIE_NHB, ORGANISATIE_IFAA,
                               GESLACHT_MAN, GESLACHT_VROUW, GESLACHT_ALLE)


LEEFTIJDSKLASSEN = (
    # WA + NHB
    # volgorde afk    geslacht        min max  kort        beschrijving               organisatie

    # 60+ (was: Veteranen)
    (61,       'VV',  GESLACHT_VROUW, 60, 0,   '60+',      '60+ Dames',               ORGANISATIE_NHB),
    (62,       'VH',  GESLACHT_MAN,   60, 0,   '60+',      '60+ Heren',               ORGANISATIE_NHB),
    (63,       'VA',  GESLACHT_ALLE,  60, 0,   '60+',      '60+ Gemengd',             ORGANISATIE_NHB),

    # 50+ (was: Master)
    (51,       'MV',  GESLACHT_VROUW, 50, 0,   '50+',      '50+ Dames',               ORGANISATIE_WA),
    (52,       'MH',  GESLACHT_MAN,   50, 0,   '50+',      '50+ Heren',               ORGANISATIE_WA),
    (53,       'MA',  GESLACHT_ALLE,  50, 0,   '50+',      '50+ Gemengd',             ORGANISATIE_NHB),

    # open klasse
    (41,       'SV',  GESLACHT_VROUW, 0, 0,    'Dames',    'Dames',                   ORGANISATIE_WA),   # 21+
    (42,       'SH',  GESLACHT_MAN,   0, 0,    'Heren',    'Heren',                   ORGANISATIE_WA),   # 21+
    (43,       'SA',  GESLACHT_ALLE,  0, 0,    'Gemengd',  'Gemengd',                 ORGANISATIE_NHB),  # 21+

    # Onder 21 (was: Junioren)
    (31,       'JV',  GESLACHT_VROUW, 0, 20,   'Onder 21', 'Onder 21 Dames',          ORGANISATIE_WA),
    (32,       'JH',  GESLACHT_MAN,   0, 20,   'Onder 21', 'Onder 21 Heren',          ORGANISATIE_WA),
    (33,       'JA',  GESLACHT_ALLE,  0, 20,   'Onder 21', 'Onder 21 Gemengd',        ORGANISATIE_NHB),

    # Onder 18 (was: Cadetten)
    (21,       'CV',  GESLACHT_VROUW, 0, 17,   'Onder 18', 'Onder 18 Dames',          ORGANISATIE_WA),
    (22,       'CH',  GESLACHT_MAN,   0, 17,   'Onder 18', 'Onder 18 Heren',          ORGANISATIE_WA),
    (23,       'CA',  GESLACHT_ALLE,  0, 17,   'Onder 18', 'Onder 18 Gemengd',        ORGANISATIE_NHB),

    # Onder 14 (was: Aspiranten)
    (15,       'AV2', GESLACHT_VROUW, 0, 13,   'Onder 14', 'Onder 14 Meisjes',        ORGANISATIE_NHB),
    (16,       'AH2', GESLACHT_MAN,   0, 13,   'Onder 14', 'Onder 14 Jongens',        ORGANISATIE_NHB),
    (17,       'AA2', GESLACHT_ALLE,  0, 13,   'Onder 14', 'Onder 14 Gemengd',        ORGANISATIE_NHB),

    # Onder 12 (was: Aspiranten)
    (11,       'AV1', GESLACHT_VROUW, 0, 11,   'Onder 12', 'Onder 12 Meisjes',        ORGANISATIE_NHB),
    (12,       'AH1', GESLACHT_MAN,   0, 11,   'Onder 12', 'Onder 12 Jongens',        ORGANISATIE_NHB),
    (13,       'AA1', GESLACHT_ALLE,  0, 11,   'Onder 12', 'Onder 12 Gemengd',        ORGANISATIE_NHB),

    # IFAA
    # volgorde afk    geslacht        min max  kort        beschrijving               organisatie

    # Senioren / 65+
    (61,       'SEV', GESLACHT_VROUW, 65, 0,   'Sen V',    'Senioren Dames (65+)',    ORGANISATIE_IFAA),
    (62,       'SEM', GESLACHT_MAN,   65, 0,   'Sen M',    'Senioren Heren (65+)',    ORGANISATIE_IFAA),

    # Veteranen / 55-64
    (51,       'VEV', GESLACHT_VROUW, 55, 0,   'Vet V',    'Veteranen Dames (55+)',   ORGANISATIE_IFAA),
    (52,       'VEM', GESLACHT_MAN,   55, 0,   'Vet M',    'Veteranen Heren (55+)',   ORGANISATIE_IFAA),

    # open klasse: Volwassenen
    (41,       'VWV', GESLACHT_VROUW, 0, 0,    'Volw V',   'Volwassen Dames',         ORGANISATIE_IFAA),
    (42,       'VWH', GESLACHT_MAN,   0, 0,    'Volw M',   'Volwassen Heren',         ORGANISATIE_IFAA),

    # Jong volwassenen (17-20)
    (31,       'JVV', GESLACHT_VROUW, 0, 20,   'Jong V',   'Jongvolwassen Dames',     ORGANISATIE_IFAA),
    (32,       'JVH', GESLACHT_MAN,   0, 20,   'Jong M',   'Jongvolwassen Heren',     ORGANISATIE_IFAA),

    # Junioren (13-16)
    (21,       'JUV', GESLACHT_VROUW, 0, 16,   'Jun V',    'Junioren Meisjes',        ORGANISATIE_IFAA),
    (22,       'JUH', GESLACHT_MAN,   0, 16,   'Jun M',    'Junioren Jongens',        ORGANISATIE_IFAA),

    # Welpen (<13)
    (11,       'WEV', GESLACHT_VROUW, 0, 12,   'Welp V',   'Welpen Meisjes',          ORGANISATIE_IFAA),
    (12,       'WEH', GESLACHT_MAN,   0, 12,   'Welp M',   'Welpen Jongens',          ORGANISATIE_IFAA),
)


KALENDERWEDSTRIJDENKLASSEN = (
    # nr  boog  lkl    afk      beschrijving
    (100, 'R',  'VA',  'R60U',  'Recurve 60+ Gemengd'),
    (101, 'R',  'VH',  'R60H',  'Recurve 60+ Heren'),
    (102, 'R',  'VV',  'R60D',  'Recurve 60+ Dames'),

    (110, 'R',  'MA',  'R50U',  'Recurve 50+ Gemengd'),
    (111, 'R',  'MH',  'R50H',  'Recurve 50+ Heren'),
    (112, 'R',  'MV',  'R50D',  'Recurve 50+ Dames'),

    (120, 'R',  'SA',  'RU',    'Recurve Gemengd'),
    (121, 'R',  'SH',  'RH',    'Recurve Heren'),
    (122, 'R',  'SV',  'RD',    'Recurve Dames'),

    (130, 'R',  'JA',  'RO21U', 'Recurve Onder 21 Gemengd'),
    (131, 'R',  'JH',  'RO21H', 'Recurve Onder 21 Heren'),
    (132, 'R',  'JV',  'RO21D', 'Recurve Onder 21 Dames'),

    (140, 'R',  'CA',  'RO18U', 'Recurve Onder 18 Gemengd'),
    (141, 'R',  'CH',  'RO18H', 'Recurve Onder 18 Heren'),
    (142, 'R',  'CV',  'RO18D', 'Recurve Onder 18 Dames'),

    (150, 'R',  'AA2', 'RO14U', 'Recurve Onder 14 Gemengd'),
    (151, 'R',  'AH2', 'RO14H', 'Recurve Onder 14 Jongens'),
    (152, 'R',  'AV2', 'RO14D', 'Recurve Onder 14 Meisjes'),

    (160, 'R',  'AA1', 'RO12U', 'Recurve Onder 12 Gemengd'),
    (161, 'R',  'AH1', 'RO12H', 'Recurve Onder 12 Jongens'),
    (162, 'R',  'AV1', 'RO12D', 'Recurve Onder 12 Meisjes'),


    (200, 'C',  'VA',  'C60U',  'Compound 60+ Gemengd'),
    (201, 'C',  'VH',  'C60H',  'Compound 60+ Heren'),
    (202, 'C',  'VV',  'C60D',  'Compound 60+ Dames'),

    (210, 'C',  'MA',  'C50U',  'Compound 50+ Gemengd'),
    (211, 'C',  'MH',  'C50H',  'Compound 50+ Heren'),
    (212, 'C',  'MV',  'C50D',  'Compound 50+ Dames'),

    (220, 'C',  'SA',  'CU',    'Compound Gemengd'),
    (221, 'C',  'SH',  'CH',    'Compound Heren'),
    (222, 'C',  'SV',  'CD',    'Compound Dames'),

    (230, 'C',  'JA',  'CO21U', 'Compound Onder 21 Gemengd'),
    (231, 'C',  'JH',  'CO21H', 'Compound Onder 21 Heren'),
    (232, 'C',  'JV',  'CO21D', 'Compound Onder 21 Dames'),

    (240, 'C',  'CA',  'CO18U', 'Compound Onder 18 Gemengd'),
    (241, 'C',  'CH',  'CO18H', 'Compound Onder 18 Heren'),
    (242, 'C',  'CV',  'CO18D', 'Compound Onder 18 Dames'),

    (250, 'C',  'AA2', 'CO14U', 'Compound Onder 14 Gemengd'),
    (251, 'C',  'AH2', 'CO14H', 'Compound Onder 14 Jongens'),
    (252, 'C',  'AV2', 'CO14D', 'Compound Onder 14 Meisjes'),

    (260, 'C',  'AA1', 'CO12U', 'Compound Onder 12 Gemengd'),
    (261, 'C',  'AH1', 'CO14H', 'Compound Onder 12 Jongens'),
    (262, 'C',  'AV1', 'CO14D', 'Compound Onder 12 Meisjes'),


    (300, 'BB', 'VA',  'B60U',  'Barebow 60+ Gemengd'),
    (301, 'BB', 'VH',  'B60H',  'Barebow 60+ Heren'),
    (302, 'BB', 'VV',  'B60D',  'Barebow 60+ Dames'),

    (310, 'BB', 'MA',  'B50U',  'Barebow 50+ Gemengd'),
    (311, 'BB', 'MH',  'B50H',  'Barebow 50+ Heren'),
    (312, 'BB', 'MV',  'B50D',  'Barebow 50+ Dames'),

    (320, 'BB', 'SA',  'BU',    'Barebow Gemengd'),
    (321, 'BB', 'SH',  'BH',    'Barebow Heren'),
    (322, 'BB', 'SV',  'BD',    'Barebow Dames'),

    (330, 'BB', 'JA',  'BO21U', 'Barebow Onder 21 Gemengd'),
    (331, 'BB', 'JH',  'BO21H', 'Barebow Onder 21 Heren'),
    (332, 'BB', 'JV',  'BO21D', 'Barebow Onder 21 Dames'),

    (340, 'BB', 'CA',  'BO18U', 'Barebow Onder 18 Gemengd'),
    (341, 'BB', 'CH',  'BO18H', 'Barebow Onder 18 Heren'),
    (342, 'BB', 'CV',  'BO18D', 'Barebow Onder 18 Dames'),

    (350, 'BB', 'AA2', 'BO14U', 'Barebow Onder 14 Gemengd'),
    (351, 'BB', 'AH2', 'BO14H', 'Barebow Onder 14 Jongens'),
    (352, 'BB', 'AV2', 'BO14D', 'Barebow Onder 14 Meisjes'),

    (360, 'BB', 'AA1', 'BO12U', 'Barebow Onder 12 Gemengd'),
    (361, 'BB', 'AH1', 'BO12H', 'Barebow Onder 12 Jongens'),
    (362, 'BB', 'AV1', 'BO12D', 'Barebow Onder 12 Meisjes'),


    (500, 'TR', 'VA',  'T60U',  'Traditional 60+ Gemengd'),
    (501, 'TR', 'VH',  'T60H',  'Traditional 60+ Heren'),
    (502, 'TR', 'VV',  'T60D',  'Traditional 60+ Dames'),

    (510, 'TR', 'MA',  'T50U',  'Traditional 50+ Gemengd'),
    (511, 'TR', 'MH',  'T50H',  'Traditional 50+ Heren'),
    (512, 'TR', 'MV',  'T50D',  'Traditional 50+ Dames'),

    (520, 'TR', 'SA',  'TU',    'Traditional Gemengd'),
    (521, 'TR', 'SH',  'TH',    'Traditional Heren'),
    (522, 'TR', 'SV',  'TD',    'Traditional Dames'),

    (530, 'TR', 'JA',  'TO21U', 'Traditional Onder 21 Gemengd'),
    (531, 'TR', 'JH',  'TO21H', 'Traditional Onder 21 Heren'),
    (532, 'TR', 'JV',  'TO21D', 'Traditional Onder 21 Dames'),

    (540, 'TR', 'CA',  'TO18U', 'Traditional Onder 18 Gemengd'),
    (541, 'TR', 'CH',  'TO18H', 'Traditional Onder 18 Heren'),
    (542, 'TR', 'CV',  'TO18D', 'Traditional Onder 18 Dames'),

    (550, 'TR', 'AA2', 'TO14U', 'Traditional Onder 14 Gemengd'),
    (551, 'TR', 'AH2', 'TO14H', 'Traditional Onder 14 Jongens'),
    (552, 'TR', 'AV2', 'TO14D', 'Traditional Onder 14 Meisjes'),

    (560, 'TR', 'AA1', 'TO12U', 'Traditional Onder 12 Gemengd'),
    (561, 'TR', 'AH1', 'TO12H', 'Traditional Onder 12 Jongens'),
    (562, 'TR', 'AV1', 'TO12D', 'Traditional Onder 12 Meisjes'),


    (600, 'LB', 'VA',  'L60U',  'Longbow 60+ Gemengd'),
    (601, 'LB', 'VH',  'L60H',  'Longbow 60+ Heren'),
    (602, 'LB', 'VV',  'L60D',  'Longbow 60+ Dames'),

    (610, 'LB', 'MA',  'L50U',  'Longbow 50+ Gemengd'),
    (611, 'LB', 'MH',  'L50H',  'Longbow 50+ Heren'),
    (612, 'LB', 'MV',  'L50D',  'Longbow 50+ Dames'),

    (620, 'LB', 'SA',  'LU',    'Longbow Gemengd'),
    (621, 'LB', 'SH',  'LH',    'Longbow Heren'),
    (622, 'LB', 'SV',  'LD',    'Longbow Dames'),

    (630, 'LB', 'JA',  'LO21U', 'Longbow Onder 21 Gemengd'),
    (631, 'LB', 'JH',  'LO21H', 'Longbow Onder 21 Heren'),
    (632, 'LB', 'JV',  'LO21D', 'Longbow Onder 21 Dames'),

    (640, 'LB', 'CA',  'LO18U', 'Longbow Onder 18 Gemengd'),
    (641, 'LB', 'CH',  'LO18H', 'Longbow Onder 18 Heren'),
    (642, 'LB', 'CV',  'LO18D', 'Longbow Onder 18 Dames'),

    (650, 'LB', 'AA2', 'LO14U', 'Longbow Onder 14 Gemengd'),
    (651, 'LB', 'AH2', 'LO14H', 'Longbow Onder 14 Jongens'),
    (652, 'LB', 'AV2', 'LO14D', 'Longbow Onder 14 Meisjes'),

    (660, 'LB', 'AA1', 'LO12U', 'Longbow Onder 12 Gemengd'),
    (661, 'LB', 'AH1', 'LO12H', 'Longbow Onder 12 Jongens'),
    (662, 'LB', 'AV1', 'LO12D', 'Longbow Onder 12 Meisjes'),
)


def update_leeftijdsklassen(apps, _):
    """ Update de leeftijdsklassen aan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    volgorde2lkl = dict()
    for lkl in leeftijdsklasse_klas.objects.all():
        volgorde2lkl[(lkl.organisatie, lkl.volgorde)] = lkl
    # for

    for volgorde, _, _, _, _, _, beschrijving, organisatie in LEEFTIJDSKLASSEN:
        lkl = volgorde2lkl[(organisatie, volgorde)]

        if beschrijving != lkl.beschrijving:
            # print('LKL: %s --> %s' % (lkl.beschrijving, beschrijving))
            lkl.beschrijving = beschrijving
            lkl.save(update_fields=['beschrijving'])
    # for


def update_kalenderwedstrijdklassen(apps, _):
    """ Update de kalender wedstrijdklassen aan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')

    volgorde2kwk = dict()        # [afkorting] = LeeftijdsKlasse
    for kwk in kalenderwedstrijdklasse_klas.objects.all():
        volgorde2kwk[kwk.volgorde] = kwk
    # for

    for volgorde, _, _, _, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
        kwk = volgorde2kwk[volgorde]

        if beschrijving != kwk.beschrijving:
            # print('KWK: %s --> %s' % (kwk.beschrijving, beschrijving))
            kwk.beschrijving = beschrijving
            kwk.save(update_fields=['beschrijving'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0049_squashed')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(update_leeftijdsklassen),
        migrations.RunPython(update_kalenderwedstrijdklassen),
    ]

# end of file
