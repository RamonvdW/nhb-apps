# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.models import (MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                               BLAZOEN_40CM, BLAZOEN_DT,
                               BLAZOEN_60CM, BLAZOEN_60CM_4SPOT)

# team wedstrijdklassen volgens spec v2.2, deel 3, tabel 3.5 + wijziging 49
WKL_TEAM = (                             # 18m                                       25m
                                         # regio1,       regio2,     rk-bk           regio1,       regio2,             rk/bk
    # 10..14 = Recurve klasse met team type 'R2' (R+BB+TR+LB)
    (15, 'Recurve klasse ERE',     'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (16, 'Recurve klasse A',       'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (17, 'Recurve klasse B',       'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (18, 'Recurve klasse C',       'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (19, 'Recurve klasse D',       'R2',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),

    (20, 'Compound klasse ERE',    'C',   (BLAZOEN_DT,),                            (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (21, 'Compound klasse A',      'C',   (BLAZOEN_DT,),                            (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    # 30 = Barebow klasse ERE met teamtype 'BB' (BB+IB+LB)
    (31, 'Barebow klasse ERE',     'BB2', (BLAZOEN_40CM,),                         (BLAZOEN_60CM,)),

    # 40 = Instinctive Bow klasse ERE / IB
    (41, 'Traditional klasse ERE', 'TR',  (BLAZOEN_40CM,),                         (BLAZOEN_60CM,)),

    (50, 'Longbow klasse ERE',     'LB',  (BLAZOEN_40CM,),                         (BLAZOEN_60CM,)),
)


# individuele wedstrijdklassen volgens spec v2.2, deel 3, tabel 3.4 + wijziging 49
WKL_INDIV = (                                                                    # regio 1      regio 2     rk/bk          25m
    (100, 'Recurve klasse 1',                              'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (101, 'Recurve klasse 2',                              'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (102, 'Recurve klasse 3',                              'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (103, 'Recurve klasse 4',                              'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (104, 'Recurve klasse 5',                              'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (105, 'Recurve klasse 6',                              'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (109, 'Recurve klasse onbekend',                       'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (110, 'Recurve Onder 21 klasse 1 (junioren)',          'R',  ('JH', 'JV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (111, 'Recurve Onder 21 klasse 2 (junioren)',          'R',  ('JH', 'JV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (119, 'Recurve Onder 21 klasse onbekend (junioren)',   'R',  ('JH', 'JV'),   (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (120, 'Recurve Onder 18 klasse 1 (cadetten)',          'R',  ('CH', 'CV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (121, 'Recurve Onder 18 klasse 2 (cadetten)',          'R',  ('CH', 'CV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (129, 'Recurve Onder 18 klasse onbekend (cadetten)',   'R',  ('CH', 'CV'),   (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (150, 'Recurve Onder 14 (aspiranten)',                 'R',  ('AH2', 'AV2'), (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),
    (155, 'Recurve Onder 12 (aspiranten)',                 'R',  ('AH1', 'AV1'), (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),


    (200, 'Compound klasse 1',                             'C',  ('SH', 'SV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (201, 'Compound klasse 2',                             'C',  ('SH', 'SV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (209, 'Compound klasse onbekend',                      'C',  ('SH', 'SV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (210, 'Compound Onder 21 klasse 1 (junioren)',         'C',  ('JH', 'JV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (211, 'Compound Onder 21 klasse 2 (junioren)',         'C',  ('JH', 'JV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (219, 'Compound Onder 21 klasse onbekend (junioren)',  'C',  ('JH', 'JV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (220, 'Compound Onder 18 klasse 1 (cadetten)',         'C',  ('CH', 'CV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (221, 'Compound Onder 18 klasse 2 (cadetten)',         'C',  ('CH', 'CV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (229, 'Compound Onder 18 klasse onbekend (cadetten)',  'C',  ('CH', 'CV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (250, 'Compound Onder 14 (aspiranten)',                'C',  ('AH2', 'AV2'), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),
    (255, 'Compound Onder 12 (aspiranten)',                'C',  ('AH1', 'AV1'), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),


    (300, 'Barebow klasse 1',                              'BB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (301, 'Barebow klasse 2',                              'BB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (309, 'Barebow klasse onbekend',                       'BB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (310, 'Barebow Jeugd klasse 1',                        'BB', ('JH', 'JV', 'CH', 'CV'), (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (350, 'Barebow Onder 14 (aspiranten)',                 'BB', ('AH2', 'AV2'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (355, 'Barebow Onder 12 (aspiranten)',                 'BB', ('AH1', 'AV1'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),


    (400, 'Instinctive Bow klasse 1',                      'IB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (401, 'Instinctive Bow klasse 2',                      'IB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (409, 'Instinctive Bow klasse onbekend',               'IB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (410, 'Instinctive Bow Jeugd klasse 1',                'IB', ('JH', 'JV', 'CH', 'CV'), (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (450, 'Instinctive Bow Onder 14 (aspiranten)',         'IB', ('AH2', 'AV2'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (455, 'Instinctive Bow Onder 12 (aspiranten)',         'IB', ('AH1', 'AV1'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),


    (500, 'Longbow klasse 1',                              'LB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (501, 'Longbow klasse 2',                              'LB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (509, 'Longbow klasse onbekend',                       'LB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (510, 'Longbow Jeugd klasse 1',                        'LB', ('JH', 'JV', 'CH', 'CV'), (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (550, 'Longbow Onder 14 (aspiranten)',                 'LB', ('AH2', 'AV2'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (555, 'Longbow Onder 12 (aspiranten)',                 'LB', ('AH1', 'AV1'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
)


WKL_INDIV_NIEUW = (                                                             # regio 1       regio 2     rk/bk
    (1100, 'Recurve klasse 1',                              'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (1101, 'Recurve klasse 2',                              'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (1102, 'Recurve klasse 3',                              'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1103, 'Recurve klasse 4',                              'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1104, 'Recurve klasse 5',                              'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1105, 'Recurve klasse 6',                              'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1109, 'Recurve klasse onbekend',                       'R',  ('SA',),       (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (1110, 'Recurve Onder 21 klasse 1 (junioren)',          'R',  ('JA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (1111, 'Recurve Onder 21 klasse 2 (junioren)',          'R',  ('JA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1119, 'Recurve Onder 21 klasse onbekend (junioren)',   'R',  ('JA',),       (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (1120, 'Recurve Onder 18 klasse 1 (cadetten)',          'R',  ('CA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1121, 'Recurve Onder 18 klasse 2 (cadetten)',          'R',  ('CA',),       (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (1129, 'Recurve Onder 18 klasse onbekend (cadetten)',   'R',  ('CA',),       (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (1150, 'Recurve Onder 14 jongens (aspiranten)',         'R',  ('AH2',),      (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),
    (1151, 'Recurve Onder 14 meisjes (aspiranten)',         'R',  ('AV2',),      (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),

    (1160, 'Recurve Onder 12 jongens (aspiranten)',         'R',  ('AH1',),      (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),
    (1161, 'Recurve Onder 12 meisjes (aspiranten)',         'R',  ('AV1',),      (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),


    (1200, 'Compound klasse 1',                             'C',  ('SA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1201, 'Compound klasse 2',                             'C',  ('SA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1209, 'Compound klasse onbekend',                      'C',  ('SA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (1210, 'Compound Onder 21 klasse 1 (junioren)',         'C',  ('JA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1211, 'Compound Onder 21 klasse 2 (junioren)',         'C',  ('JA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1219, 'Compound Onder 21 klasse onbekend (junioren)',  'C',  ('JA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (1220, 'Compound Onder 18 klasse 1 (cadetten)',         'C',  ('CA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1221, 'Compound Onder 18 klasse 2 (cadetten)',         'C',  ('CA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (1229, 'Compound Onder 18 klasse onbekend (cadetten)',  'C',  ('CA',),       (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (1250, 'Compound Onder 14 jongens (aspiranten)',        'C',  ('AH2',),      (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),
    (1251, 'Compound Onder 14 meisjes (aspiranten)',        'C',  ('AV2',),      (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),

    (1260, 'Compound Onder 12 jongens (aspiranten)',        'C',  ('AH1',),      (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),
    (1261, 'Compound Onder 12 meisjes (aspiranten)',        'C',  ('AV1',),      (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),


    (1300, 'Barebow klasse 1',                              'BB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1301, 'Barebow klasse 2',                              'BB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1309, 'Barebow klasse onbekend',                       'BB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1310, 'Barebow Jeugd klasse 1',                        'BB', ('JA', 'CA'),  (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1350, 'Barebow Onder 14 jongens (aspiranten)',         'BB', ('AH2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1351, 'Barebow Onder 14 meisjes (aspiranten)',         'BB', ('AV2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),

    (1360, 'Barebow Onder 12 jongens (aspiranten)',         'BB', ('AH1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1361, 'Barebow Onder 12 meisjes (aspiranten)',         'BB', ('AV1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),


    (1400, 'Traditional klasse 1',                          'TR', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1401, 'Traditional klasse 2',                          'TR', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1409, 'Traditional klasse onbekend',                   'TR', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1410, 'Traditional Jeugd klasse 1',                    'TR', ('JA', 'CA'),  (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1450, 'Traditional Onder 14 jongens (aspiranten)',     'TR', ('AH2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1451, 'Traditional Onder 14 meisjes (aspiranten)',     'TR', ('AV2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),

    (1460, 'Traditional Onder 12 jongens (aspiranten)',     'TR', ('AH1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1461, 'Traditional Onder 12 meisjes (aspiranten)',     'TR', ('AV1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),


    (1500, 'Longbow klasse 1',                              'LB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1501, 'Longbow klasse 2',                              'LB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (1509, 'Longbow klasse onbekend',                       'LB', ('SA',),       (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1510, 'Longbow Jeugd klasse 1',                        'LB', ('JA', 'CA'),  (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (1550, 'Longbow Onder 14 jongens (aspiranten)',         'LB', ('AH2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1551, 'Longbow Onder 14 meisjes (aspiranten)',         'LB', ('AV2',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),

    (1555, 'Longbow Onder 12 jongens (aspiranten)',         'LB', ('AH1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (1556, 'Longbow Onder 12 meisjes (aspiranten)',         'LB', ('AV1',),      (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
)


KALENDERWEDSTRIJDENKLASSEN = (
    # old new  boog afk
    (0,   100, 'R', 'VA', 'Recurve 60+ (veteraan)'),
    (100, 101, 'R', 'VH', 'Recurve 60+ mannen (veteraan)'),
    (101, 102, 'R', 'VV', 'Recurve 60+ vrouwen (veteraan)'),

    (0,   110, 'R', 'MA', 'Recurve 50+ (master)'),
    (110, 111, 'R', 'MH', 'Recurve 50+ mannen (master)'),
    (111, 112, 'R', 'MV', 'Recurve 50+ vrouwen (master)'),

    (0,   120, 'R', 'SA', 'Recurve (senior)'),
    (120, 121, 'R', 'SH', 'Recurve mannen (senior)'),
    (121, 122, 'R', 'SV', 'Recurve vrouwen (senior)'),

    (0,   130, 'R', 'JA', 'Recurve Onder 21 (junior)'),
    (130, 131, 'R', 'JH', 'Recurve Onder 21 mannen (junior)'),
    (131, 132, 'R', 'JV', 'Recurve Onder 21 vrouwen (junior)'),

    (0,   140, 'R', 'CH', 'Recurve Onder 18 (cadet)'),
    (140, 141, 'R', 'CH', 'Recurve Onder 18 jongens (cadet)'),
    (141, 142, 'R', 'CV', 'Recurve Onder 18 meisjes (cadet)'),

    (0,   150, 'R', 'AA2', 'Recurve Onder 14 (aspirant)'),
    (150, 151, 'R', 'AH2', 'Recurve Onder 14 jongens (aspirant)'),
    (151, 152, 'R', 'AV2', 'Recurve Onder 14 meisjes (aspirant)'),


    (0,   200, 'C', 'VA', 'Compound 60+ (veteraan)'),
    (200, 201, 'C', 'VH', 'Compound 60+ mannen (veteraan)'),
    (201, 202, 'C', 'VV', 'Compound 60+ vrouwen (veteraan)'),

    (0,   210, 'C', 'MA', 'Compound 50+ (master)'),
    (210, 211, 'C', 'MH', 'Compound 50+ mannen (master)'),
    (211, 212, 'C', 'MV', 'Compound 50+ vrouwen (master)'),

    (0,   220, 'C', 'SA', 'Compound (senior)'),
    (220, 221, 'C', 'SH', 'Compound mannen (senior)'),
    (221, 222, 'C', 'SV', 'Compound vrouwen (senior)'),

    (0,   230, 'C', 'JA', 'Compound Onder 21 (junior)'),
    (230, 231, 'C', 'JH', 'Compound Onder 21 mannen (junior)'),
    (231, 232, 'C', 'JV', 'Compound Onder 21 vrouwen (junior)'),

    (0,   240, 'C', 'CA', 'Compound Onder 18 (cadet)'),
    (240, 241, 'C', 'CH', 'Compound Onder 18 jongens (cadet)'),
    (241, 242, 'C', 'CV', 'Compound Onder 18 meisjes (cadet)'),

    (0,   250, 'C', 'AA2', 'Compound Onder 14 (aspirant)'),
    (250, 251, 'C', 'AH2', 'Compound Onder 14 jongens (aspirant)'),
    (251, 252, 'C', 'AV2', 'Compound Onder 14 meisjes (aspirant)'),


    (0,   300, 'BB', 'VA', 'Barebow 60+ (veteraan)'),
    (300, 301, 'BB', 'VH', 'Barebow 60+ mannen (veteraan)'),
    (301, 302, 'BB', 'VV', 'Barebow 60+ vrouwen (veteraan)'),

    (0,   310, 'BB', 'MA', 'Barebow 50+ (master)'),
    (310, 311, 'BB', 'MH', 'Barebow 50+ mannen (master)'),
    (311, 312, 'BB', 'MV', 'Barebow 50+ vrouwen (master)'),

    (0,   320, 'BB', 'SA', 'Barebow (senior)'),
    (320, 321, 'BB', 'SH', 'Barebow mannen (senior)'),
    (321, 322, 'BB', 'SV', 'Barebow vrouwen (senior)'),

    (0,   330, 'BB', 'JA', 'Barebow Onder 21 (junior)'),
    (330, 331, 'BB', 'JH', 'Barebow Onder 21 mannen (junior)'),
    (331, 332, 'BB', 'JV', 'Barebow Onder 21 vrouwen (junior)'),

    (0,   340, 'BB', 'CA', 'Barebow Onder 18 (cadet)'),
    (340, 341, 'BB', 'CH', 'Barebow Onder 18 jongens (cadet)'),
    (341, 342, 'BB', 'CV', 'Barebow Onder 18 meisjes (cadet)'),

    (0,   350, 'BB', 'AA2', 'Barebow Onder 14 (aspirant)'),
    (350, 351, 'BB', 'AH2', 'Barebow Onder 14 jongens (aspirant)'),
    (351, 352, 'BB', 'AV2', 'Barebow Onder 14 meisjes (aspirant)'),


    (0,   400, 'IB', 'VA', 'Instinctive Bow 60+ (veteraan)'),
    (400, 401, 'IB', 'VH', 'Instinctive Bow 60+ mannen (veteraan)'),
    (401, 402, 'IB', 'VV', 'Instinctive Bow 60+ vrouwen (veteraan)'),

    (0,   410, 'IB', 'MA', 'Instinctive Bow 50+ (master)'),
    (410, 411, 'IB', 'MH', 'Instinctive Bow 50+ mannen (master)'),
    (411, 412, 'IB', 'MV', 'Instinctive Bow 50+ vrouwen (master)'),

    (0,   420, 'IB', 'SA', 'Instinctive Bow (senior)'),
    (420, 421, 'IB', 'SH', 'Instinctive Bow mannen (senior)'),
    (421, 422, 'IB', 'SV', 'Instinctive Bow vrouwen (senior)'),

    (0,   430, 'IB', 'JA', 'Instinctive Bow Onder 21 (junior)'),
    (430, 431, 'IB', 'JH', 'Instinctive Bow Onder 21 mannen (junior)'),
    (431, 432, 'IB', 'JV', 'Instinctive Bow Onder 21 vrouwen (junior)'),

    (0,   440, 'IB', 'CA', 'Instinctive Bow Onder 18 (cadet)'),
    (440, 441, 'IB', 'CH', 'Instinctive Bow Onder 18 jongens (cadet)'),
    (441, 442, 'IB', 'CV', 'Instinctive Bow Onder 18 meisjes (cadet)'),

    (0,   450, 'IB', 'AA2', 'Instinctive Bow Onder 14 (aspirant)'),
    (450, 451, 'IB', 'AH2', 'Instinctive Bow Onder 14 jongens (aspirant)'),
    (451, 452, 'IB', 'AV2', 'Instinctive Bow Onder 14 meisjes (aspirant)'),


    (0,   500, 'IB', 'VA', 'Traditional 60+ (veteraan)'),
    (0,   501, 'IB', 'VH', 'Traditional 60+ mannen (veteraan)'),
    (0,   502, 'IB', 'VV', 'Traditional 60+ vrouwen (veteraan)'),

    (0,   510, 'IB', 'MA', 'Traditional 50+ (master)'),
    (0,   511, 'IB', 'MH', 'Traditional 50+ mannen (master)'),
    (0,   512, 'IB', 'MV', 'Traditional 50+ vrouwen (master)'),

    (0,   520, 'IB', 'SA', 'Traditional (senior)'),
    (0,   521, 'IB', 'SH', 'Traditional mannen (senior)'),
    (0,   522, 'IB', 'SV', 'Traditional vrouwen (senior)'),

    (0,   530, 'IB', 'JA', 'Traditional Onder 21 (junior)'),
    (0,   531, 'IB', 'JH', 'Traditional Onder 21 mannen (junior)'),
    (0,   532, 'IB', 'JV', 'Traditional Onder 21 vrouwen (junior)'),

    (0,   540, 'IB', 'CA', 'Traditional Onder 18 (cadet)'),
    (0,   541, 'IB', 'CH', 'Traditional Onder 18 jongens (cadet)'),
    (0,   542, 'IB', 'CV', 'Traditional Onder 18 meisjes (cadet)'),

    (0,   550, 'IB', 'AA2', 'Traditional Onder 14 (aspirant)'),
    (0,   551, 'IB', 'AH2', 'Traditional Onder 14 14 jongens (aspirant)'),
    (0,   552, 'IB', 'AV2', 'Traditional Onder 14 meisjes (aspirant)'),


    (0,   600, 'LB', 'VA', 'Longbow 60+ (veteraan)'),
    (500, 601, 'LB', 'VH', 'Longbow 60+ mannen (veteraan)'),
    (501, 602, 'LB', 'VV', 'Longbow 60+ vrouwen (veteraan)'),

    (0,   610, 'LB', 'MA', 'Longbow 50+ (master)'),
    (510, 611, 'LB', 'MH', 'Longbow 50+ mannen (master)'),
    (511, 612, 'LB', 'MV', 'Longbow 50+ vrouwen (master)'),

    (0,   620, 'LB', 'SA', 'Longbow (senior)'),
    (520, 621, 'LB', 'SH', 'Longbow mannen (senior)'),
    (521, 622, 'LB', 'SV', 'Longbow vrouwen (senior)'),

    (0,   630, 'LB', 'JA', 'Longbow Onder 21 (junior)'),
    (530, 631, 'LB', 'JH', 'Longbow Onder 21 mannen (junior)'),
    (531, 632, 'LB', 'JV', 'Longbow Onder 21 vrouwen (junior)'),

    (0,   640, 'LB', 'CA', 'Longbow Onder 18 (cadet)'),
    (540, 641, 'LB', 'CH', 'Longbow Onder 18 jongens (cadet)'),
    (541, 642, 'LB', 'CV', 'Longbow Onder 18 meisjes (cadet)'),

    (0,   650, 'LB', 'AA2', 'Longbow Onder 14 (aspirant)'),
    (550, 651, 'LB', 'AH2', 'Longbow Onder 14 jongens (aspirant)'),
    (551, 652, 'LB', 'AV2', 'Longbow Onder 14 meisjes (aspirant)'),
)


def update_boogtypen(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')
    sporterboog_klas = apps.get_model('Sporter', 'SporterBoog')

    # maak de nieuwe boogtype aan
    # K plaatst deze tussen BB en IB
    boog_tr = boogtype_klas(afkorting='TR', volgorde='K', beschrijving='Traditional')
    boog_tr.save()

    # kopieer elke SporterBoog(IB) naar SporterBoog(TR)
    bulk = list()
    for sporterboog_ib in sporterboog_klas.objects.filter(boogtype__afkorting='IB'):        # pragma: no cover

        # maak een TR variant van deze IB
        obj = sporterboog_klas(
                    sporter=sporterboog_ib.sporter,
                    boogtype=boog_tr,
                    heeft_interesse=sporterboog_ib.heeft_interesse,
                    voor_wedstrijd=sporterboog_ib.voor_wedstrijd)
        bulk.append(obj)
    # for

    sporterboog_klas.objects.bulk_create(bulk)


def update_leeftijdsklassen(apps, _):
    """ Hernoem de leeftijdsklassen en voeg genderneutrale klassen toe """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    rename = {
        'VH':  (62, '60+',      '60+ mannen (veteranen)'),
        'VV':  (61, '60+',      '60+ vrouwen (veteranen)'),
        'MH':  (52, '50+',      '50+ mannen (masters)'),
        'MV':  (51, '50+',      '50+ vrouwen (masters)'),
        'SH':  (42, '21+',      '21+ mannen (senioren)'),
        'SV':  (41, '21+',      '21+ vrouwen (senioren)'),
        'JH':  (32, 'Onder 21', 'Onder 21 mannen (junioren)'),
        'JV':  (31, 'Onder 21', 'Onder 21 vrouwen (junioren)'),
        'CH':  (22, 'Onder 18', 'Onder 18 jongens (cadetten)'),
        'CV':  (21, 'Onder 18', 'Onder 18 meisjes (cadetten)'),
        'AH2': (16, 'Onder 14', 'Onder 14 jongens (aspiranten)'),
        'AV2': (15, 'Onder 14', 'Onder 14 meisjes (aspiranten)'),
        'AH1': (12, 'Onder 12', 'Onder 12 jongens (aspiranten)'),
        'AV1': (11, 'Onder 12', 'Onder 12 meisjes (aspiranten)'),
    }

    for lkl in leeftijdsklasse_klas.objects.all():
        volgorde, kort, lang = rename[lkl.afkorting]
        lkl.volgorde = volgorde
        lkl.klasse_kort = kort
        lkl.beschrijving = lang
        lkl.save(update_fields=['volgorde', 'klasse_kort', 'beschrijving'])
    # for

    # nieuwe genderneutrale leeftijdsklassen
    bulk = [
        # 60+
        leeftijdsklasse_klas(
            afkorting='VA', geslacht='A',
            klasse_kort='60+',
            beschrijving='60+ (veteranen)',
            volgorde=63,
            min_wedstrijdleeftijd=60,
            max_wedstrijdleeftijd=0,
            volgens_wa=False),

        # 50+
        leeftijdsklasse_klas(
            afkorting='MA', geslacht='A',
            klasse_kort='50+',
            beschrijving='50+ (masters)',
            volgorde=53,
            min_wedstrijdleeftijd=50,
            max_wedstrijdleeftijd=0,
            volgens_wa=False),

        # 21+
        leeftijdsklasse_klas(
            afkorting='SA', geslacht='A',
            klasse_kort='21+',
            beschrijving='21+ (senioren)',
            volgorde=43,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=0,
            volgens_wa=False),

        # Onder 21
        leeftijdsklasse_klas(
            afkorting='JA', geslacht='A',
            klasse_kort='Onder 21',
            beschrijving='Onder 21 (junioren)',
            volgorde=33,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20,
            volgens_wa=False),

        # Onder 18
        leeftijdsklasse_klas(
            afkorting='CA', geslacht='A',
            klasse_kort='Onder 18',
            beschrijving='Onder 18 (cadetten)',
            volgorde=23,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=17,
            volgens_wa=False),

        # Onder 14
        leeftijdsklasse_klas(
            afkorting='AA2', geslacht='A',
            klasse_kort='Onder 14',
            beschrijving='Onder 14 (aspiranten)',
            volgorde=17,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=13,
            volgens_wa=False),

        # Onder 12
        leeftijdsklasse_klas(
            afkorting='AA1', geslacht='A',
            klasse_kort='Onder 12',
            beschrijving='Onder 12 (aspiranten)',
            volgorde=13,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=11,
            volgens_wa=False),
    ]
    leeftijdsklasse_klas.objects.bulk_create(bulk)


def update_team_typen(apps, _):
    """ Pas de team typen aan """

    # team typen volgens spec v2.2 wijziging 49 (deel 3, tabel 3.3)

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    boog_type_klas = apps.get_model('BasisTypen', 'BoogType')

    boog_r = boog_bb = boog_tr = boog_lb = None
    for boog in boog_type_klas.objects.all():
        if boog.afkorting == 'R':
            boog_r = boog
        if boog.afkorting == 'BB':
            boog_bb = boog
        if boog.afkorting == 'TR':
            boog_tr = boog
        if boog.afkorting == 'LB':
            boog_lb = boog
    # for

    # maak de standaard team typen aan
    team_r2 = team_type_klas(afkorting='R2', volgorde='1', beschrijving='Recurve team')
    team_bb2 = team_type_klas(afkorting='BB2', volgorde='3', beschrijving='Barebow team')
    team_tr = team_type_klas(afkorting='TR', volgorde='4', beschrijving='Traditional team')

    team_type_klas.objects.bulk_create([team_r2, team_bb2, team_tr])

    team_r2.boog_typen.add(boog_r, boog_bb, boog_tr, boog_lb)
    team_bb2.boog_typen.add(boog_bb, boog_tr, boog_lb)
    team_tr.boog_typen.add(boog_tr, boog_lb)


def update_wedstrijdklassen_individueel(apps, _):
    """ Pas de individuele wedstrijdklassen aan"""

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'IndivWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # maak look-up tabellen
    volgorde2klasse = dict()
    for klasse in indiv_wedstrijdklasse_klas.objects.all():
        volgorde2klasse[klasse.volgorde] = klasse
    # for

    boog_afkorting2boogtype = dict()
    for lkl_obj in boogtype_klas.objects.all():
        boog_afkorting2boogtype[lkl_obj.afkorting] = lkl_obj
    # for

    lkl_afkorting2leeftijdsklasse = dict()
    for lkl in leeftijdsklasse_klas.objects.all():
        lkl_afkorting2leeftijdsklasse[lkl.afkorting] = lkl
    # for

    for tup in WKL_INDIV:
        volgorde, beschrijving = tup[:2]
        klasse = volgorde2klasse[volgorde]

        # nieuwe beschrijving + stel buiten gebruik
        klasse.buiten_gebruik = True
        klasse.beschrijving = beschrijving
        klasse.save(update_fields=['beschrijving', 'buiten_gebruik'])
    # for

    # nieuwe klassen toevoegen
    volgorde2lkl = dict()
    bulk = list()
    for tup in WKL_INDIV_NIEUW:
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

        wkl = indiv_wedstrijdklasse_klas(
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

    indiv_wedstrijdklasse_klas.objects.bulk_create(bulk)

    # koppel nu de leeftijdsklassen aan elke wedstrijdklasse
    for wkl in indiv_wedstrijdklasse_klas.objects.exclude(buiten_gebruik=True):
        lkl_lijst = volgorde2lkl[wkl.volgorde]
        wkl.leeftijdsklassen.set(lkl_lijst)
    # for


def update_wedstrijdklassen_team(apps, _):
    """ Pas de team wedstrijdklassen aan"""

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    team_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'TeamWedstrijdklasse')

    # maak een look-up table voor de team type afkortingen
    boog_afkorting2teamtype = dict()
    for team_type in team_type_klas.objects.all():
        boog_afkorting2teamtype[team_type.afkorting] = team_type
    # for

    # zoek alle bestaande team wedstrijdklassen
    # en zet niet meer gewenste wedstrijdklassen op "buiten_gebruik"
    volgordes = [volgorde for volgorde, beschrijving, teamtype_afkorting, blazoenen_18m, blazoenen_25m in WKL_TEAM]
    volgorde2wkl = dict()
    for wkl in team_wedstrijdklasse_klas.objects.all():
        if wkl.volgorde not in volgordes:
            wkl.buiten_gebruik = True
            wkl.save(update_fields=['buiten_gebruik'])
        volgorde2wkl[wkl.volgorde] = wkl
    # for
    del volgordes, wkl

    bulk = list()
    for volgorde, beschrijving, teamtype_afkorting, blazoenen_18m, blazoenen_25m in WKL_TEAM:

        if volgorde in volgorde2wkl.keys():
            # bestaat al
            pass
        else:
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

            wkl = team_wedstrijdklasse_klas(
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

            bulk.append(wkl)
    # for

    team_wedstrijdklasse_klas.objects.bulk_create(bulk)


def update_kalenderwedstrijdklassen(apps, _):
    """ Pas de kalender wedstrijdklassen aan """

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

    volgorde2klasse = dict()
    for klasse in kalenderwedstrijdklasse_klas.objects.all():
        volgorde2klasse[klasse.volgorde] = klasse
    # for

    bulk = list()
    for volgorde_oud, volgorde_nieuw, boog_afk, lkl_afk, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
        if volgorde_oud == 0:
            boog = afk2boog[boog_afk]
            lkl = afk2lkl[lkl_afk]
            obj = kalenderwedstrijdklasse_klas(
                            beschrijving=beschrijving,
                            boogtype=boog,
                            leeftijdsklasse=lkl,
                            volgorde=volgorde_nieuw)
            bulk.append(obj)
        else:
            klasse = volgorde2klasse[volgorde_oud]
            klasse.volgorde = volgorde_nieuw
            klasse.beschrijving = beschrijving
            klasse.save(update_fields=['volgorde', 'beschrijving'])
    # for
    kalenderwedstrijdklasse_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0025_indexes'),
        ('Sporter', 'm0005_geslacht_anders')
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='leeftijdsklasse',
            name='geslacht',
            field=models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw'), ('A', 'Alle')], max_length=1),
        ),
        migrations.AlterField(
            model_name='teamtype',
            name='afkorting',
            field=models.CharField(max_length=3),
        ),
        migrations.RunPython(update_boogtypen),
        migrations.RunPython(update_leeftijdsklassen),
        migrations.RunPython(update_team_typen),
        migrations.RunPython(update_wedstrijdklassen_individueel),
        migrations.RunPython(update_wedstrijdklassen_team),
        migrations.RunPython(update_kalenderwedstrijdklassen),
    ]

# end of file
