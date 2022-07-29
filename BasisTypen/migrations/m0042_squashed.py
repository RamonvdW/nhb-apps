# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.models import (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_60CM, BLAZOEN_60CM_4SPOT,
                               ORGANISATIE_NHB, GESLACHT_MAN, GESLACHT_VROUW, GESLACHT_ALLE)


# team competitie klassen volgens spec v2.2, deel 3, tabel 3.5
TEAM_COMP_KLASSEN = (                    # 18m                                       25m
                                         # regio1,       regio2,     rk-bk           regio1,       regio2,             rk/bk
    (15, 'Recurve klasse ERE',     'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (16, 'Recurve klasse A',       'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (17, 'Recurve klasse B',       'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (18, 'Recurve klasse C',       'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (19, 'Recurve klasse D',       'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),

    (20, 'Compound klasse ERE',    'C',   (BLAZOEN_DT,),                            (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (21, 'Compound klasse A',      'C',   (BLAZOEN_DT,),                            (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (31, 'Barebow klasse ERE',     'BB2', (BLAZOEN_40CM,),                          (BLAZOEN_60CM,)),

    (41, 'Traditional klasse ERE', 'TR',  (BLAZOEN_40CM,),                          (BLAZOEN_60CM,)),

    (50, 'Longbow klasse ERE',     'LB',  (BLAZOEN_40CM,),                          (BLAZOEN_60CM,)),
)

# individuele competitie klassen volgens spec v2.2, deel 3, tabel 3.4
INDIV_COMP_KLASSEN = (                        # boog   lkl            regio 1       regio 2     rk/bk
    (1100, 'Recurve klasse 1',                  'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (1101, 'Recurve klasse 2',                  'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (1102, 'Recurve klasse 3',                  'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1103, 'Recurve klasse 4',                  'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1104, 'Recurve klasse 5',                  'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1105, 'Recurve klasse 6',                  'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1109, 'Recurve klasse onbekend',           'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (1110, 'Recurve Onder 21 klasse 1',         'R',  ('JA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (1111, 'Recurve Onder 21 klasse 2',         'R',  ('JA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1119, 'Recurve Onder 21 klasse onbekend',  'R',  ('JA',),       (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (1120, 'Recurve Onder 18 klasse 1',         'R',  ('CA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1121, 'Recurve Onder 18 klasse 2',         'R',  ('CA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1129, 'Recurve Onder 18 klasse onbekend',  'R',  ('CA',),       (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (1150, 'Recurve Onder 14 jongens',          'R',  ('AH2',),      (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),
    (1151, 'Recurve Onder 14 meisjes',          'R',  ('AV2',),      (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),

    (1160, 'Recurve Onder 12 jongens',          'R',  ('AH1',),      (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),
    (1161, 'Recurve Onder 12 meisjes',          'R',  ('AV1',),      (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),


    (1200, 'Compound klasse 1',                 'C',  ('SA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1201, 'Compound klasse 2',                 'C',  ('SA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1209, 'Compound klasse onbekend',          'C',  ('SA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (1210, 'Compound Onder 21 klasse 1',        'C',  ('JA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1211, 'Compound Onder 21 klasse 2',        'C',  ('JA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1219, 'Compound Onder 21 klasse onbekend', 'C',  ('JA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (1220, 'Compound Onder 18 klasse 1',        'C',  ('CA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1221, 'Compound Onder 18 klasse 2',        'C',  ('CA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1229, 'Compound Onder 18 klasse onbekend', 'C',  ('CA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (1250, 'Compound Onder 14 jongens',         'C',  ('AH2',),      (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),
    (1251, 'Compound Onder 14 meisjes',         'C',  ('AV2',),      (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),

    (1260, 'Compound Onder 12 jongens',         'C',  ('AH1',),      (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),
    (1261, 'Compound Onder 12 meisjes',         'C',  ('AV1',),      (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),


    (1300, 'Barebow klasse 1',                  'BB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1301, 'Barebow klasse 2',                  'BB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1309, 'Barebow klasse onbekend',           'BB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1310, 'Barebow Jeugd klasse 1',            'BB', ('JA', 'CA'),  (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1350, 'Barebow Onder 14 jongens',          'BB', ('AH2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1351, 'Barebow Onder 14 meisjes',          'BB', ('AV2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),

    (1360, 'Barebow Onder 12 jongens',          'BB', ('AH1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1361, 'Barebow Onder 12 meisjes',          'BB', ('AV1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),


    (1400, 'Traditional klasse 1',              'TR', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1401, 'Traditional klasse 2',              'TR', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1409, 'Traditional klasse onbekend',       'TR', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1410, 'Traditional Jeugd klasse 1',        'TR', ('JA', 'CA'),  (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1450, 'Traditional Onder 14 jongens',      'TR', ('AH2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1451, 'Traditional Onder 14 meisjes',      'TR', ('AV2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),

    (1460, 'Traditional Onder 12 jongens',      'TR', ('AH1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1461, 'Traditional Onder 12 meisjes',      'TR', ('AV1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),


    (1500, 'Longbow klasse 1',                  'LB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1501, 'Longbow klasse 2',                  'LB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1509, 'Longbow klasse onbekend',           'LB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1510, 'Longbow Jeugd klasse 1',            'LB', ('JA', 'CA'),  (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1550, 'Longbow Onder 14 jongens',          'LB', ('AH2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1551, 'Longbow Onder 14 meisjes',          'LB', ('AV2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),

    (1555, 'Longbow Onder 12 jongens',          'LB', ('AH1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1556, 'Longbow Onder 12 meisjes',          'LB', ('AV1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
)


KALENDERWEDSTRIJDENKLASSEN = (
    # nr  boog afk
    (100, 'R', 'VA', 'R60U', 'Recurve 60+'),
    (101, 'R', 'VH', 'R60H', 'Recurve 60+ heren'),
    (102, 'R', 'VV', 'R60D', 'Recurve 60+ dames'),

    (110, 'R', 'MA', 'R50U', 'Recurve 50+'),
    (111, 'R', 'MH', 'R50H', 'Recurve 50+ heren'),
    (112, 'R', 'MV', 'R50D', 'Recurve 50+ dames'),

    (120, 'R', 'SA', 'RU', 'Recurve'),
    (121, 'R', 'SH', 'RH', 'Recurve heren'),
    (122, 'R', 'SV', 'RD', 'Recurve dames'),

    (130, 'R', 'JA', 'RO21U', 'Recurve Onder 21'),
    (131, 'R', 'JH', 'RO21H', 'Recurve Onder 21 heren'),
    (132, 'R', 'JV', 'RO21D', 'Recurve Onder 21 dames'),

    (140, 'R', 'CA', 'RO18U', 'Recurve Onder 18'),
    (141, 'R', 'CH', 'RO18H', 'Recurve Onder 18 jongens'),
    (142, 'R', 'CV', 'RO18D', 'Recurve Onder 18 meisjes'),

    (150, 'R', 'AA2', 'RO14U', 'Recurve Onder 14'),
    (151, 'R', 'AH2', 'RO14H', 'Recurve Onder 14 jongens'),
    (152, 'R', 'AV2', 'RO14D', 'Recurve Onder 14 meisjes'),

    (160, 'R', 'AA1', 'RO12U', 'Recurve Onder 12'),
    (161, 'R', 'AH1', 'RO12H', 'Recurve Onder 12 jongens'),
    (162, 'R', 'AV1', 'RO12D', 'Recurve Onder 12 meisjes'),


    (200, 'C', 'VA', 'C60U', 'Compound 60+'),
    (201, 'C', 'VH', 'C60H', 'Compound 60+ heren'),
    (202, 'C', 'VV', 'C60D', 'Compound 60+ dames'),

    (210, 'C', 'MA', 'C50U', 'Compound 50+'),
    (211, 'C', 'MH', 'C50H', 'Compound 50+ heren'),
    (212, 'C', 'MV', 'C50D', 'Compound 50+ dames'),

    (220, 'C', 'SA', 'CU', 'Compound'),
    (221, 'C', 'SH', 'CH', 'Compound heren'),
    (222, 'C', 'SV', 'CD', 'Compound dames'),

    (230, 'C', 'JA', 'CO21U', 'Compound Onder 21'),
    (231, 'C', 'JH', 'CO21H', 'Compound Onder 21 heren'),
    (232, 'C', 'JV', 'CO21D', 'Compound Onder 21 dames'),

    (240, 'C', 'CA', 'CO18U', 'Compound Onder 18'),
    (241, 'C', 'CH', 'CO18H', 'Compound Onder 18 jongens'),
    (242, 'C', 'CV', 'CO18D', 'Compound Onder 18 meisjes'),

    (250, 'C', 'AA2', 'CO14U', 'Compound Onder 14'),
    (251, 'C', 'AH2', 'CO14H', 'Compound Onder 14 jongens'),
    (252, 'C', 'AV2', 'CO14D', 'Compound Onder 14 meisjes'),

    (260, 'C', 'AA1', 'CO12U', 'Compound Onder 12'),
    (261, 'C', 'AH1', 'CO14H', 'Compound Onder 12 jongens'),
    (262, 'C', 'AV1', 'CO14D', 'Compound Onder 12 meisjes'),


    (300, 'BB', 'VA', 'B60U', 'Barebow 60+'),
    (301, 'BB', 'VH', 'B60H', 'Barebow 60+ heren'),
    (302, 'BB', 'VV', 'B60D', 'Barebow 60+ dames'),

    (310, 'BB', 'MA', 'B50U', 'Barebow 50+'),
    (311, 'BB', 'MH', 'B50H', 'Barebow 50+ heren'),
    (312, 'BB', 'MV', 'B50D', 'Barebow 50+ dames'),

    (320, 'BB', 'SA', 'BU', 'Barebow'),
    (321, 'BB', 'SH', 'BH', 'Barebow heren'),
    (322, 'BB', 'SV', 'BD', 'Barebow dames'),

    (330, 'BB', 'JA', 'BO21U', 'Barebow Onder 21'),
    (331, 'BB', 'JH', 'BO21H', 'Barebow Onder 21 heren'),
    (332, 'BB', 'JV', 'BO21D', 'Barebow Onder 21 dames'),

    (340, 'BB', 'CA', 'BO18U', 'Barebow Onder 18'),
    (341, 'BB', 'CH', 'BO18H', 'Barebow Onder 18 jongens'),
    (342, 'BB', 'CV', 'BO18D', 'Barebow Onder 18 meisjes'),

    (350, 'BB', 'AA2', 'BO14U', 'Barebow Onder 14'),
    (351, 'BB', 'AH2', 'BO14H', 'Barebow Onder 14 jongens'),
    (352, 'BB', 'AV2', 'BO14D', 'Barebow Onder 14 meisjes'),

    (360, 'BB', 'AA1', 'BO12U', 'Barebow Onder 12'),
    (361, 'BB', 'AH1', 'BO12H', 'Barebow Onder 12 jongens'),
    (362, 'BB', 'AV1', 'BO12D', 'Barebow Onder 12 meisjes'),


    (500, 'TR', 'VA', 'T60', 'Traditional 60+'),
    (501, 'TR', 'VH', 'T60', 'Traditional 60+ heren'),
    (502, 'TR', 'VV', 'T60', 'Traditional 60+ dames'),

    (510, 'TR', 'MA', 'T50', 'Traditional 50+'),
    (511, 'TR', 'MH', 'T50', 'Traditional 50+ heren'),
    (512, 'TR', 'MV', 'T50', 'Traditional 50+ dames'),

    (520, 'TR', 'SA', 'T', 'Traditional'),
    (521, 'TR', 'SH', 'T', 'Traditional heren'),
    (522, 'TR', 'SV', 'T', 'Traditional dames'),

    (530, 'TR', 'JA', 'TO', 'Traditional Onder 21'),
    (531, 'TR', 'JH', 'TO', 'Traditional Onder 21 heren'),
    (532, 'TR', 'JV', 'TO', 'Traditional Onder 21 dames'),

    (540, 'TR', 'CA', 'TO', 'Traditional Onder 18'),
    (541, 'TR', 'CH', 'TO', 'Traditional Onder 18 jongens'),
    (542, 'TR', 'CV', 'TO', 'Traditional Onder 18 meisjes'),

    (550, 'TR', 'AA2', 'TO', 'Traditional Onder 14'),
    (551, 'TR', 'AH2', 'TO', 'Traditional Onder 14 jongens'),
    (552, 'TR', 'AV2', 'TO', 'Traditional Onder 14 meisjes'),

    (560, 'TR', 'AA1', 'TO', 'Traditional Onder 12'),
    (561, 'TR', 'AH1', 'TO', 'Traditional Onder 12 jongens'),
    (562, 'TR', 'AV1', 'TO', 'Traditional Onder 12 meisjes'),


    (600, 'LB', 'VA', 'L60U', 'Longbow 60+'),
    (601, 'LB', 'VH', 'L60H', 'Longbow 60+ heren'),
    (602, 'LB', 'VV', 'L60D', 'Longbow 60+ dames'),

    (610, 'LB', 'MA', 'L50U', 'Longbow 50+'),
    (611, 'LB', 'MH', 'L50H', 'Longbow 50+ heren'),
    (612, 'LB', 'MV', 'L50D', 'Longbow 50+ dames'),

    (620, 'LB', 'SA', 'LU', 'Longbow'),
    (621, 'LB', 'SH', 'LH', 'Longbow heren'),
    (622, 'LB', 'SV', 'LD', 'Longbow dames'),

    (630, 'LB', 'JA', 'LO21U', 'Longbow Onder 21'),
    (631, 'LB', 'JH', 'LO21H', 'Longbow Onder 21 heren'),
    (632, 'LB', 'JV', 'LO21D', 'Longbow Onder 21 dames'),

    (640, 'LB', 'CA', 'LO18U', 'Longbow Onder 18'),
    (641, 'LB', 'CH', 'LO18H', 'Longbow Onder 18 jongens'),
    (642, 'LB', 'CV', 'LO18D', 'Longbow Onder 18 meisjes'),

    (650, 'LB', 'AA2', 'LO14U', 'Longbow Onder 14'),
    (651, 'LB', 'AH2', 'LO14H', 'Longbow Onder 14 jongens'),
    (652, 'LB', 'AV2', 'LO14D', 'Longbow Onder 14 meisjes'),

    (660, 'LB', 'AA1', 'LO12U', 'Longbow Onder 12'),
    (661, 'LB', 'AH1', 'LO12H', 'Longbow Onder 12 jongens'),
    (662, 'LB', 'AV1', 'LO12D', 'Longbow Onder 12 meisjes'),
)


def init_boogtypen(apps, _):
    """ Maak de boog typen aan """

    # boog typen volgens spec v2.2, tabel 3.2

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    ifaa = 'F'  # International Field Archery Association

    # maak de standaard boogtypen aan
    bulk = [boogtype_klas(pk=1, afkorting='R',  volgorde='A', beschrijving='Recurve'),
            boogtype_klas(pk=2, afkorting='C',  volgorde='D', beschrijving='Compound'),
            boogtype_klas(pk=3, afkorting='BB', volgorde='I', beschrijving='Barebow'),
            # oud: boogtype IB met pk=4
            boogtype_klas(pk=5, afkorting='LB', volgorde='S', beschrijving='Longbow'),
            boogtype_klas(pk=6, afkorting='TR', volgorde='K', beschrijving='Traditional'),
            boogtype_klas(pk=7, organisatie=ifaa, afkorting='BBR', volgorde='A', beschrijving='Barebow Recurve'),
            boogtype_klas(pk=8, organisatie=ifaa, afkorting='BBC', volgorde='B', beschrijving='Barebow Compound'),
            boogtype_klas(pk=9, organisatie=ifaa, afkorting='FSR', volgorde='F', beschrijving='Freestyle Limited Recurve'),
            boogtype_klas(pk=10, organisatie=ifaa, afkorting='FSC', volgorde='G', beschrijving='Freestyle Limited Compound'),
            boogtype_klas(pk=11, organisatie=ifaa, afkorting='FU',  volgorde='H', beschrijving='Freestyle Unlimited'),
            boogtype_klas(pk=12, organisatie=ifaa, afkorting='BHR', volgorde='K', beschrijving='Bowhunter Recurve'),
            boogtype_klas(pk=13, organisatie=ifaa, afkorting='BHC', volgorde='L', beschrijving='Bowhunter Compound'),
            boogtype_klas(pk=14, organisatie=ifaa, afkorting='BHU', volgorde='M', beschrijving='Bowhunter Unlimited'),
            boogtype_klas(pk=15, organisatie=ifaa, afkorting='BHL', volgorde='N', beschrijving='Bowhunter Limited'),
            boogtype_klas(pk=16, organisatie=ifaa, afkorting='ITR', volgorde='P', beschrijving='Traditional Recurve Bow'),
            boogtype_klas(pk=17, organisatie=ifaa, afkorting='ILB', volgorde='R', beschrijving='Longbow'),
            boogtype_klas(pk=18, organisatie=ifaa, afkorting='IHB', volgorde='T', beschrijving='Historical Bow')]

    boogtype_klas.objects.bulk_create(bulk)


def init_leeftijdsklassen(apps, _):
    """ Maak de leeftijdsklassen aan """

    # leeftijdsklassen volgens spec v2.1, deel 3, tabel 3.1

    # note: wedstrijdleeftijd = leeftijd die je bereikt in een jaar
    #       competitieleeftijd = wedstrijdleeftijd + 1

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    ifaa = 'F'  # International Field Archery Association

    bulk = [
        # 60+
        leeftijdsklasse_klas(
            afkorting='VV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='60+',
            beschrijving='60+ vrouwen (veteranen)',
            volgorde=61,
            min_wedstrijdleeftijd=60,
            max_wedstrijdleeftijd=0,
            organisatie=ORGANISATIE_NHB),
        leeftijdsklasse_klas(
            afkorting='VH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='60+',
            beschrijving='60+ mannen (veteranen)',
            volgorde=62,
            min_wedstrijdleeftijd=60,
            max_wedstrijdleeftijd=0,
            organisatie=ORGANISATIE_NHB),
        leeftijdsklasse_klas(
            afkorting='VA',
            wedstrijd_geslacht=GESLACHT_ALLE,
            klasse_kort='60+',
            beschrijving='60+ (veteranen)',
            volgorde=63,
            min_wedstrijdleeftijd=60,
            max_wedstrijdleeftijd=0,
            organisatie=ORGANISATIE_NHB),

        # 50+
        leeftijdsklasse_klas(
            afkorting='MV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='50+',
            beschrijving='50+ vrouwen (masters)',
            volgorde=51,
            min_wedstrijdleeftijd=50,
            max_wedstrijdleeftijd=0),
        leeftijdsklasse_klas(
            afkorting='MH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='50+',
            beschrijving='50+ mannen (masters)',
            volgorde=52,
            min_wedstrijdleeftijd=50,
            max_wedstrijdleeftijd=0),
        leeftijdsklasse_klas(
            afkorting='MA',
            wedstrijd_geslacht=GESLACHT_ALLE,
            klasse_kort='50+',
            beschrijving='50+ (masters)',
            volgorde=53,
            min_wedstrijdleeftijd=50,
            max_wedstrijdleeftijd=0,
            organisatie=ORGANISATIE_NHB),

        # open klasse
        leeftijdsklasse_klas(
            afkorting='SV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='21+',
            beschrijving='21+ vrouwen (senioren)',
            volgorde=41,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=0),
        leeftijdsklasse_klas(
            afkorting='SH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='21+',
            beschrijving='21+ mannen (senioren)',
            volgorde=42,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=0),
        leeftijdsklasse_klas(
            afkorting='SA',
            wedstrijd_geslacht=GESLACHT_ALLE,
            klasse_kort='21+',
            beschrijving='21+ (senioren)',
            volgorde=43,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=0,
            organisatie=ORGANISATIE_NHB),

        # Onder 21
        leeftijdsklasse_klas(
            afkorting='JV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Onder 21',
            beschrijving='Onder 21 vrouwen',
            volgorde=31,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20),
        leeftijdsklasse_klas(
            afkorting='JH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Onder 21',
            beschrijving='Onder 21 mannen',
            volgorde=32,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20),
        leeftijdsklasse_klas(
            afkorting='JA',
            wedstrijd_geslacht=GESLACHT_ALLE,
            klasse_kort='Onder 21',
            beschrijving='Onder 21',
            volgorde=33,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20,
            organisatie=ORGANISATIE_NHB),

        # Onder 18
        leeftijdsklasse_klas(
            afkorting='CV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Onder 18',
            beschrijving='Onder 18 meisjes',
            volgorde=21,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=17),
        leeftijdsklasse_klas(
            afkorting='CH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Onder 18',
            beschrijving='Onder 18 jongens',
            volgorde=22,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=17),
        leeftijdsklasse_klas(
            afkorting='CA',
            wedstrijd_geslacht=GESLACHT_ALLE,
            klasse_kort='Onder 18',
            beschrijving='Onder 18',
            volgorde=23,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=17,
            organisatie=ORGANISATIE_NHB),

        # Onder 14
        leeftijdsklasse_klas(
            afkorting='AV2',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Onder 14',
            beschrijving='Onder 14 meisjes',
            volgorde=15,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=13,
            organisatie=ORGANISATIE_NHB),
        leeftijdsklasse_klas(
            afkorting='AH2',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Onder 14',
            beschrijving='Onder 14 jongens',
            volgorde=16,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=13,
            organisatie=ORGANISATIE_NHB),
        leeftijdsklasse_klas(
            afkorting='AA2',
            wedstrijd_geslacht=GESLACHT_ALLE,
            klasse_kort='Onder 14',
            beschrijving='Onder 14',
            volgorde=17,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=13,
            organisatie=ORGANISATIE_NHB),

        # Onder 12
        leeftijdsklasse_klas(
            afkorting='AV1',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Onder 12',
            beschrijving='Onder 12 meisjes',
            volgorde=11,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=11,
            organisatie=ORGANISATIE_NHB),
        leeftijdsklasse_klas(
            afkorting='AH1',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Onder 12',
            beschrijving='Onder 12 jongens',
            volgorde=12,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=11,
            organisatie=ORGANISATIE_NHB),
        leeftijdsklasse_klas(
            afkorting='AA1',
            wedstrijd_geslacht=GESLACHT_ALLE,
            klasse_kort='Onder 12',
            beschrijving='Onder 12',
            volgorde=13,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=11,
            organisatie=ORGANISATIE_NHB),

        # IFAA

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
            beschrijving='Volwassen mannen',
            volgorde=42,
            min_wedstrijdleeftijd=21,
            max_wedstrijdleeftijd=54),

        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='VWV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Volw V',
            beschrijving='Volwassen vrouwen',
            volgorde=41,
            min_wedstrijdleeftijd=21,
            max_wedstrijdleeftijd=54),

        # Jong volwassenen (17-20)
        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='JVH',
            wedstrijd_geslacht=GESLACHT_MAN,
            klasse_kort='Jong M',
            beschrijving='Jongvolwassen mannen',
            volgorde=32,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20),

        leeftijdsklasse_klas(
            organisatie=ifaa,
            afkorting='JVV',
            wedstrijd_geslacht=GESLACHT_VROUW,
            klasse_kort='Jong V',
            beschrijving='Jongvolwassen vrouwen',
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
            beschrijving='Welpen jongens',
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


def init_team_typen(apps, _):
    """ Maak de team typen aan """

    # team typen volgens spec v2.2 (deel 3, tabel 3.3)

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    boog_type_klas = apps.get_model('BasisTypen', 'BoogType')

    boog_r = boog_c = boog_bb = boog_tr = boog_lb = None
    for boog in boog_type_klas.objects.all():
        if boog.afkorting == 'R':
            boog_r = boog
        if boog.afkorting == 'C':
            boog_c = boog
        if boog.afkorting == 'BB':
            boog_bb = boog
        if boog.afkorting == 'TR':
            boog_tr = boog
        if boog.afkorting == 'LB':
            boog_lb = boog
    # for

    # oud: 'R'  met boogtype IB + BB + R
    # oud: 'BB' met boogtype IB + BB
    # oud: 'IB' met boogtype IB

    # maak de standaard team typen aan
    team_r2 = team_type_klas(afkorting='R2', volgorde=1, beschrijving='Recurve team')
    team_c = team_type_klas(afkorting='C',  volgorde=2, beschrijving='Compound team')
    team_bb2 = team_type_klas(afkorting='BB2', volgorde=3, beschrijving='Barebow team')
    # R, C en BB zijn officiële WA team typen, de rest is nationaal - deze zijn default al op WA gezet
    team_tr = team_type_klas(afkorting='TR', volgorde=4, beschrijving='Traditional team', organisatie=ORGANISATIE_NHB)
    team_lb = team_type_klas(afkorting='LB', volgorde=5, beschrijving='Longbow team', organisatie=ORGANISATIE_NHB)

    team_type_klas.objects.bulk_create([team_r2, team_c, team_bb2, team_tr, team_lb])

    team_r2.boog_typen.add(boog_r, boog_bb, boog_tr, boog_lb)
    team_c.boog_typen.add(boog_c)
    team_bb2.boog_typen.add(boog_bb, boog_tr, boog_lb)
    team_tr.boog_typen.add(boog_tr, boog_lb)
    team_lb.boog_typen.add(boog_lb)


def init_wedstrijdklassen_individueel(apps, _):
    """ Maak de wedstrijdklassen aan"""

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_comp_klasse_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # maak een look-up table voor de boog afkortingen
    boog_afkorting2boogtype = dict()
    for lkl_obj in boogtype_klas.objects.all():
        boog_afkorting2boogtype[lkl_obj.afkorting] = lkl_obj
    # for

    lkl_afkorting2leeftijdsklasse = dict()
    for lkl in leeftijdsklasse_klas.objects.all():
        lkl_afkorting2leeftijdsklasse[lkl.afkorting] = lkl
    # for

    volgorde2lkl = dict()

    bulk = list()
    for tup in INDIV_COMP_KLASSEN:
        if len(tup) == 6:
            volgorde, beschrijving, boog_afkorting, leeftijdsklassen_afkortingen, blazoenen_18m, blazoenen_25m = tup
            niet_voor_rk_bk = False
        else:
            volgorde, beschrijving, boog_afkorting, leeftijdsklassen_afkortingen, blazoenen_18m, blazoenen_25m, niet_voor_rk_bk = tup

        is_onbekend = 'onbekend' in beschrijving
        if is_onbekend:
            niet_voor_rk_bk = True

        boogtype_obj = boog_afkorting2boogtype[boog_afkorting]

        # blazoen is 1 of 3 lang
        blazoenen_18m = list(blazoenen_18m)
        while len(blazoenen_18m) < 3:
            blazoenen_18m.append(blazoenen_18m[0])
        # while

        blazoenen_25m = list(blazoenen_25m)
        while len(blazoenen_25m) < 3:
            blazoenen_25m.append(blazoenen_25m[0])
        # while

        wkl = indiv_comp_klasse_klas(
                    beschrijving=beschrijving,
                    volgorde=volgorde,
                    boogtype=boogtype_obj,
                    niet_voor_rk_bk=niet_voor_rk_bk,
                    is_onbekend=is_onbekend,
                    blazoen1_18m_regio=blazoenen_18m[0],
                    blazoen2_18m_regio=blazoenen_18m[1],
                    blazoen_18m_rk_bk=blazoenen_18m[2],
                    blazoen1_25m_regio=blazoenen_25m[0],
                    blazoen2_25m_regio=blazoenen_25m[1],
                    blazoen_25m_rk_bk=blazoenen_25m[2])

        # koppel de gewenste leeftijdsklassen aan de wedstrijdklasse
        # en vlag de aspirant klassen
        volgorde2lkl[volgorde] = lkl_lijst = list()
        for lkl_afkorting in leeftijdsklassen_afkortingen:
            lkl = lkl_afkorting2leeftijdsklasse[lkl_afkorting]

            # vlag aspirant klassen
            if lkl.afkorting[0] == 'A':     # AA, AH, AV
                wkl.is_aspirant_klasse = True

            lkl_lijst.append(lkl)
        # for

        bulk.append(wkl)
    # for

    indiv_comp_klasse_klas.objects.bulk_create(bulk)

    # koppel nu de leeftijdsklassen aan elke wedstrijdklasse
    for wkl in indiv_comp_klasse_klas.objects.all():
        lkl_lijst = volgorde2lkl[wkl.volgorde]
        wkl.leeftijdsklassen.set(lkl_lijst)
    # for


def init_wedstrijdklassen_team(apps, _):
    """ Maak de team wedstrijdklassen aan"""

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    team_comp_klasse_klas = apps.get_model('BasisTypen', 'TemplateCompetitieTeamKlasse')

    # maak een look-up table voor de team type afkortingen
    boog_afkorting2teamtype = dict()
    for team_type in team_type_klas.objects.all():
        boog_afkorting2teamtype[team_type.afkorting] = team_type
    # for

    bulk = list()
    for volgorde, beschrijving, teamtype_afkorting, blazoenen_18m, blazoenen_25m in TEAM_COMP_KLASSEN:

        teamtype = boog_afkorting2teamtype[teamtype_afkorting]

        # blazoenen_18m is 1 of 3 lang
        blazoenen_18m = list(blazoenen_18m)
        while len(blazoenen_18m) < 3:
            blazoenen_18m.append(blazoenen_18m[-1])

        # blazoenen_25m is 1 of 3 lang (1 = repeated up to 3), daarna: 1+2 voor regio en 3 voor rk/bk
        blazoenen_25m = list(blazoenen_25m)
        while len(blazoenen_25m) < 3:
            blazoenen_25m.append(blazoenen_25m[0])
        # while

        obj = team_comp_klasse_klas(
                    beschrijving=beschrijving,
                    volgorde=volgorde,
                    team_type=teamtype,
                    blazoen1_18m_regio=blazoenen_18m[0],
                    blazoen2_18m_regio=blazoenen_18m[1],
                    blazoen1_18m_rk_bk=blazoenen_18m[2],
                    blazoen2_18m_rk_bk=blazoenen_18m[2],
                    blazoen1_25m_regio=blazoenen_25m[0],
                    blazoen2_25m_regio=blazoenen_25m[1],
                    blazoen_25m_rk_bk=blazoenen_25m[2])

        bulk.append(obj)
    # for

    team_comp_klasse_klas.objects.bulk_create(bulk)


def init_kalenderwedstrijdklassen(apps, _):
    """ Maak de kalender wedstrijdklassen aan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    afk2boog = dict()       # [afkorting] = BoogType
    for boog in boogtype_klas.objects.all():
        afk2boog[boog.afkorting] = boog
    # for

    afk2lkl = dict()        # [afkorting] = LeeftijdsKlasse
    for lkl in leeftijdsklasse_klas.objects.all():
        afk2lkl[lkl.afkorting] = lkl
    # for

    bulk = list()
    for volgorde, boog_afk, lkl_afk, afkorting, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
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


def init_kalenderwedstrijdklassen_ifaa(apps, _):
    """ Maak de IFAA kalender wedstrijdklassen aan """

    # vertaling eigen afkorting naar code in internationale wedstrijdklasse
    ifaa_afkorting_leeftijd = {
        'SEM': 'SM',
        'SEV': 'SF',
        'VEM': 'VM',
        'VEV': 'VF',
        'VWH': 'AM',
        'VWV': 'AF',
        'JVH': 'YAM',
        'JVV': 'YAF',
        'JUH': 'JM',
        'JUV': 'JF',
        'WEH': 'CM',
        'WEV': 'CF',
    }

    # vertaling eigen afkorting naar code in internationale wedstrijdklasse
    ifaa_afkorting_boog = {
        'BBR': 'BB-R',
        'BBC': 'BB-C',
        'FSR': 'FS-R',
        'FSC': 'FS-C',
        'FU': 'FU',
        'BHR': 'BH-R',
        'BHC': 'BH-C',
        'BHU': 'BU',
        'BHL': 'BL',
        'ITR': 'TR',
        'ILB': 'LB',
        'IHB': 'HB',
    }

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')
    ifaa = 'F'  # International Field Archery Association

    # haal de bogen en leeftijden op en sorteer meteen op de gewenste volgorde
    bogen = boogtype_klas.objects.filter(organisatie=ifaa).order_by('volgorde')
    leeftijden = leeftijdsklasse_klas.objects.filter(organisatie=ifaa).order_by('-volgorde')

    # maak elke combinatie van leeftijdsklassen en boogtype aan
    bulk = list()
    groep_volgorde = 1000
    for boog in bogen:
        volgorde = groep_volgorde
        for leeftijd in leeftijden:
            beschrijving = '%s %s' % (boog.beschrijving, leeftijd.beschrijving)
            afkorting = ifaa_afkorting_leeftijd[leeftijd.afkorting] + ifaa_afkorting_boog[boog.afkorting]

            bulk.append(
                kalenderwedstrijdklasse_klas(
                    organisatie=ifaa,
                    beschrijving=beschrijving,
                    boogtype=boog,
                    leeftijdsklasse=leeftijd,
                    afkorting=afkorting,
                    volgorde=volgorde)
            )
            volgorde += 1
        # for

        groep_volgorde += 100
    # for

    kalenderwedstrijdklasse_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('BasisTypen', 'm0028_squashed'),
                ('BasisTypen', 'm0029_template'),
                ('BasisTypen', 'm0030_organisatie'),
                ('BasisTypen', 'm0031_repair_tr'),
                ('BasisTypen', 'm0032_organisatie_nhb'),
                ('BasisTypen', 'm0033_buiten_gebruik'),
                ('BasisTypen', 'm0034_ifaa_bogen'),
                ('BasisTypen', 'm0035_team_buiten_gebruik'),
                ('BasisTypen', 'm0036_corrigeer_kalender_140'),
                ('BasisTypen', 'm0037_ifaa_leeftijdsklassen'),
                ('BasisTypen', 'm0038_ifaa_wedstrijdklassen'),
                ('BasisTypen', 'm0039_ifaa_afkortingen'),
                ('BasisTypen', 'm0040_nhb_onder12'),
                ('BasisTypen', 'm0041_ifaa_volwassenen')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = []

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BoogType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=50)),
                ('afkorting', models.CharField(max_length=5)),
                ('volgorde', models.CharField(default='?', max_length=1)),
                ('organisatie', models.CharField(choices=[('W', 'World Archery'), ('N', 'NHB'), ('F', 'IFAA')], default='W', max_length=1)),
                ('buiten_gebruik', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Boog type',
                'verbose_name_plural': 'Boog types',
            },
        ),
        migrations.CreateModel(
            name='LeeftijdsKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('afkorting', models.CharField(max_length=5)),
                ('beschrijving', models.CharField(max_length=80)),
                ('klasse_kort', models.CharField(max_length=30)),
                ('wedstrijd_geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw'), ('A', 'Genderneutraal')], max_length=1)),
                ('min_wedstrijdleeftijd', models.IntegerField()),
                ('max_wedstrijdleeftijd', models.IntegerField()),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('organisatie', models.CharField(choices=[('W', 'World Archery'), ('N', 'NHB'), ('F', 'IFAA')], default='W', max_length=1)),
            ],
            options={
                'verbose_name': 'Leeftijdsklasse',
                'verbose_name_plural': 'Leeftijdsklassen',
            },
        ),
        migrations.CreateModel(
            name='TeamType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=50)),
                ('afkorting', models.CharField(max_length=3)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('boog_typen', models.ManyToManyField(to='BasisTypen.BoogType')),
                ('organisatie', models.CharField(choices=[('W', 'World Archery'), ('N', 'NHB'), ('F', 'IFAA')], default='W', max_length=1)),
                ('buiten_gebruik', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Team type',
                'verbose_name_plural': 'Team typen',
            },
        ),
        migrations.CreateModel(
            name='TemplateCompetitieIndivKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('niet_voor_rk_bk', models.BooleanField()),
                ('is_onbekend', models.BooleanField(default=False)),
                ('boogtype', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('leeftijdsklassen', models.ManyToManyField(to='BasisTypen.LeeftijdsKlasse')),
                ('blazoen1_18m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen1_25m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
                ('blazoen2_18m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen2_25m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
                ('blazoen_18m_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen_25m_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
                ('is_aspirant_klasse', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Template Competitie Indiv Klasse',
                'verbose_name_plural': 'Template Competitie Indiv Klassen'
            },
        ),
        migrations.CreateModel(
            name='TemplateCompetitieTeamKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('team_type', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='BasisTypen.teamtype')),
                ('blazoen1_25m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
                ('blazoen2_25m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
                ('blazoen1_18m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen2_18m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen1_18m_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen2_18m_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen_25m_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
            ],
            options={
                'verbose_name': 'Template Competitie Team Klasse',
                'verbose_name_plural': 'Template Competitie Team Klassen'
            },
        ),
        migrations.CreateModel(
            name='KalenderWedstrijdklasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('boogtype', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('leeftijdsklasse', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.leeftijdsklasse')),
                ('organisatie', models.CharField(choices=[('W', 'World Archery'), ('N', 'NHB'), ('F', 'IFAA')], default='W', max_length=1)),
                ('afkorting', models.CharField(default='?', max_length=10)),
            ],
            options={
                'verbose_name': 'Kalender Wedstrijdklasse',
                'verbose_name_plural': 'Kalender Wedstrijdklassen'
            },
        ),
        migrations.RunPython(init_boogtypen),
        migrations.RunPython(init_leeftijdsklassen),
        migrations.RunPython(init_team_typen),
        migrations.RunPython(init_wedstrijdklassen_individueel),
        migrations.RunPython(init_wedstrijdklassen_team),
        migrations.RunPython(init_kalenderwedstrijdklassen),
        migrations.RunPython(init_kalenderwedstrijdklassen_ifaa),
        migrations.AddIndex(
            model_name='boogtype',
            index=models.Index(fields=['afkorting'], name='BasisTypen__afkorti_0bf4b9_idx'),
        ),
        migrations.AddIndex(
            model_name='boogtype',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_81dcc1_idx'),
        ),
        migrations.AddIndex(
            model_name='teamtype',
            index=models.Index(fields=['afkorting'], name='BasisTypen__afkorti_6ad4da_idx'),
        ),
        migrations.AddIndex(
            model_name='teamtype',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_4984e4_idx'),
        ),
        migrations.AddIndex(
            model_name='kalenderwedstrijdklasse',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_246cec_idx'),
        ),
        migrations.AddIndex(
            model_name='templatecompetitieindivklasse',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_48eb00_idx'),
        ),
        migrations.AddIndex(
            model_name='templatecompetitieteamklasse',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_4d62f0_idx'),
        ),
    ]

# end of file
