# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion
from BasisTypen.models import (MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                               BLAZOEN_40CM, BLAZOEN_DT,
                               BLAZOEN_60CM, BLAZOEN_60CM_4SPOT)


# team wedstrijdklassen volgens spec v2.1, deel 3, tabel 3.5
WKL_TEAM = (                                 # 18m                                     # 25m
                                             # regio1/2, rk-bk                         # regio1, regio2, rk/bk
    (10, 'Recurve klasse ERE',         'R',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),        # R = team type
    (11, 'Recurve klasse A',           'R',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM),  (BLAZOEN_60CM,)),
    (12, 'Recurve klasse B',           'R',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM),  (BLAZOEN_60CM,)),
    (13, 'Recurve klasse C',           'R',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM),  (BLAZOEN_60CM,)),
    (14, 'Recurve klasse D',           'R',  (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM),  (BLAZOEN_60CM,)),

    (20, 'Compound klasse ERE',        'C',  (BLAZOEN_DT,),                             (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (21, 'Compound klasse A',          'C',  (BLAZOEN_DT,),                             (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (30, 'Barebow klasse ERE',         'BB', (BLAZOEN_40CM,),                           (BLAZOEN_60CM,)),

    (40, 'Instinctive Bow klasse ERE', 'IB', (BLAZOEN_40CM,),                           (BLAZOEN_60CM,)),

    (50, 'Longbow klasse ERE',         'LB', (BLAZOEN_40CM,),                           (BLAZOEN_60CM,)),
)

# individuele wedstrijdklassen volgens spec v2.1, deel 3, tabel 3.4
WKL_INDIV = (
    (100, 'Recurve klasse 1',                      'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (101, 'Recurve klasse 2',                      'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (102, 'Recurve klasse 3',                      'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (103, 'Recurve klasse 4',                      'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (104, 'Recurve klasse 5',                      'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (105, 'Recurve klasse 6',                      'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (109, 'Recurve klasse onbekend',               'R',  ('SH', 'SV'),   (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (110, 'Recurve Junioren klasse 1',             'R',  ('JH', 'JV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_DT),   (BLAZOEN_60CM,)),
    (111, 'Recurve Junioren klasse 2',             'R',  ('JH', 'JV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (119, 'Recurve Junioren klasse onbekend',      'R',  ('JH', 'JV'),   (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (120, 'Recurve Cadetten klasse 1',             'R',  ('CH', 'CV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (121, 'Recurve Cadetten klasse 2',             'R',  ('CH', 'CV'),   (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_40CM), (BLAZOEN_60CM,)),
    (129, 'Recurve Cadetten klasse onbekend',      'R',  ('CH', 'CV'),   (BLAZOEN_40CM, BLAZOEN_DT),               (BLAZOEN_60CM,)),

    (150, 'Recurve Aspiranten 11-12 jaar',         'R',  ('AH2', 'AV2'), (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),
    (155, 'Recurve Aspiranten < 11 jaar',          'R',  ('AH1', 'AV1'), (BLAZOEN_60CM,),                          (BLAZOEN_60CM,), True),


    (200, 'Compound klasse 1',                     'C',  ('SH', 'SV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (201, 'Compound klasse 2',                     'C',  ('SH', 'SV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (209, 'Compound klasse onbekend',              'C',  ('SH', 'SV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (210, 'Compound Junioren klasse 1',            'C',  ('JH', 'JV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (211, 'Compound Junioren klasse 2',            'C',  ('JH', 'JV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (219, 'Compound Junioren klasse onbekend',     'C',  ('JH', 'JV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (220, 'Compound Cadetten klasse 1',            'C',  ('CH', 'CV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (221, 'Compound Cadetten klasse 2',            'C',  ('CH', 'CV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (229, 'Compound Cadetten klasse onbekend',     'C',  ('CH', 'CV'),   (BLAZOEN_DT,),                                    (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (250, 'Compound Aspiranten 11-12 jaar',        'C',  ('AH2', 'AV2'), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),
    (255, 'Compound Aspiranten < 11 jaar',         'C',  ('AH1', 'AV1'), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM), (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT), True),


    (300, 'Barebow klasse 1',                      'BB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (301, 'Barebow klasse 2',                      'BB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (309, 'Barebow klasse onbekend',               'BB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (310, 'Barebow Jeugd klasse 1',                'BB', ('JH', 'JV', 'CH', 'CV'), (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (350, 'Barebow Aspiranten 11-12 jaar',         'BB', ('AH2', 'AV2'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (355, 'Barebow Aspiranten < 11 jaar',          'BB', ('AH1', 'AV1'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),


    (400, 'Instinctive Bow klasse 1',              'IB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (401, 'Instinctive Bow klasse 2',              'IB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (409, 'Instinctive Bow klasse onbekend',       'IB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (410, 'Instinctive Bow Jeugd klasse 1',        'IB', ('JH', 'JV', 'CH', 'CV'), (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (450, 'Instinctive Bow Aspiranten 11-12 jaar', 'IB', ('AH2', 'AV2'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (455, 'Instinctive Bow Aspiranten < 11 jaar',  'IB', ('AH1', 'AV1'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),


    (500, 'Longbow klasse 1',                      'LB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (501, 'Longbow klasse 2',                      'LB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),
    (509, 'Longbow klasse onbekend',               'LB', ('SH', 'SV'),             (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (510, 'Longbow Jeugd klasse 1',                'LB', ('JH', 'JV', 'CH', 'CV'), (BLAZOEN_40CM,), (BLAZOEN_60CM,)),

    (550, 'Longbow Aspiranten 11-12 jaar',         'LB', ('AH2', 'AV2'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
    (555, 'Longbow Aspiranten < 11 jaar',          'LB', ('AH1', 'AV1'),           (BLAZOEN_60CM,), (BLAZOEN_60CM,), True),
)


KALENDERWEDSTRIJDENKLASSEN = (
    (100, 'R', 'VH', 'Recurve veteraan mannen'),
    (101, 'R', 'VV', 'Recurve veteraan vrouwen'),

    (110, 'R', 'MH', 'Recurve master mannen'),
    (111, 'R', 'MV', 'Recurve master vrouwen'),

    (120, 'R', 'SH', 'Recurve senior mannen'),
    (121, 'R', 'SV', 'Recurve senior vrouwen'),

    (130, 'R', 'JH', 'Recurve junior mannen'),
    (131, 'R', 'JV', 'Recurve junior vrouwen'),

    (140, 'R', 'CH', 'Recurve cadet jongens'),
    (141, 'R', 'CV', 'Recurve cadet meisjes'),

    (150, 'R', 'AH2', 'Recurve aspirant jongens'),
    (151, 'R', 'AV2', 'Recurve aspirant meisjes'),


    (200, 'C', 'VH', 'Compound veteraan mannen'),
    (201, 'C', 'VV', 'Compound veteraan vrouwen'),

    (210, 'C', 'MH', 'Compound master mannen'),
    (211, 'C', 'MV', 'Compound master vrouwen'),

    (220, 'C', 'SH', 'Compound senior mannen'),
    (221, 'C', 'SV', 'Compound senior vrouwen'),

    (230, 'C', 'JH', 'Compound junior mannen'),
    (231, 'C', 'JV', 'Compound junior vrouwen'),

    (240, 'C', 'CH', 'Compound cadet jongens'),
    (241, 'C', 'CV', 'Compound cadet meisjes'),

    (250, 'C', 'AH2', 'Compound aspirant jongens'),
    (251, 'C', 'AV2', 'Compound aspirant meisjes'),


    (300, 'BB', 'VH', 'Barebow veteraan mannen'),
    (301, 'BB', 'VV', 'Barebow veteraan vrouwen'),

    (310, 'BB', 'MH', 'Barebow master mannen'),
    (311, 'BB', 'MV', 'Barebow master vrouwen'),

    (320, 'BB', 'SH', 'Barebow senior mannen'),
    (321, 'BB', 'SV', 'Barebow senior vrouwen'),

    (330, 'BB', 'JH', 'Barebow junior mannen'),
    (331, 'BB', 'JV', 'Barebow junior vrouwen'),

    (340, 'BB', 'CH', 'Barebow cadet jongens'),
    (341, 'BB', 'CV', 'Barebow cadet meisjes'),

    (350, 'BB', 'AH2', 'Barebow aspirant jongens'),
    (351, 'BB', 'AV2', 'Barebow aspirant meisjes'),


    (400, 'IB', 'VH', 'Instinctive Bow veteraan mannen'),
    (401, 'IB', 'VV', 'Instinctive Bow veteraan vrouwen'),

    (410, 'IB', 'MH', 'Instinctive Bow master mannen'),
    (411, 'IB', 'MV', 'Instinctive Bow master vrouwen'),

    (420, 'IB', 'SH', 'Instinctive Bow senior mannen'),
    (421, 'IB', 'SV', 'Instinctive Bow senior vrouwen'),

    (430, 'IB', 'JH', 'Instinctive Bow junior mannen'),
    (431, 'IB', 'JV', 'Instinctive Bow junior vrouwen'),

    (440, 'IB', 'CH', 'Instinctive Bow cadet jongens'),
    (441, 'IB', 'CV', 'Instinctive Bow cadet meisjes'),

    (450, 'IB', 'AH2', 'Instinctive Bow aspirant jongens'),
    (451, 'IB', 'AV2', 'Instinctive Bow aspirant meisjes'),


    (500, 'LB', 'VH', 'Longbow veteraan mannen'),
    (501, 'LB', 'VV', 'Longbow veteraan vrouwen'),

    (510, 'LB', 'MH', 'Longbow master mannen'),
    (511, 'LB', 'MV', 'Longbow master vrouwen'),

    (520, 'LB', 'SH', 'Longbow senior mannen'),
    (521, 'LB', 'SV', 'Longbow senior vrouwen'),

    (530, 'LB', 'JH', 'Longbow junior mannen'),
    (531, 'LB', 'JV', 'Longbow junior vrouwen'),

    (540, 'LB', 'CH', 'Longbow cadet jongens'),
    (541, 'LB', 'CV', 'Longbow cadet meisjes'),

    (550, 'LB', 'AH2', 'Longbow aspirant jongens'),
    (551, 'LB', 'AV2', 'Longbow aspirant meisjes'),
)


def init_boogtype(apps, _):
    """ Maak de boog typen aan """

    # boog typen volgens spec v2.1, tabel 3.2

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # maak de standaard boogtypen aan
    bulk = [boogtype_klas(afkorting='R',  volgorde='A', beschrijving='Recurve'),
            boogtype_klas(afkorting='C',  volgorde='D', beschrijving='Compound'),
            boogtype_klas(afkorting='BB', volgorde='I', beschrijving='Barebow'),
            boogtype_klas(afkorting='IB', volgorde='M', beschrijving='Instinctive bow'),
            boogtype_klas(afkorting='LB', volgorde='S', beschrijving='Longbow')]
    boogtype_klas.objects.bulk_create(bulk)


def init_leeftijdsklasse(apps, _):
    """ Maak de leeftijdsklassen aan """

    # leeftijdsklassen volgens spec v2.1, deel 3, tabel 3.1

    # note: wedstrijdleeftijd = leeftijd die je bereikt in een jaar
    #       competitieleeftijd = wedstrijdleeftijd + 1

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    bulk = [
        # >= 60
        leeftijdsklasse_klas(
            afkorting='VH', geslacht='M',
            klasse_kort='Veteraan',
            beschrijving='Veteranen, mannen',
            volgorde=60,
            min_wedstrijdleeftijd=60,
            max_wedstrijdleeftijd=0,
            volgens_wa=False),
        leeftijdsklasse_klas(
            afkorting='VV', geslacht='V',
            klasse_kort='Veteraan',
            beschrijving='Veteranen, vrouwen',
            volgorde=60,
            min_wedstrijdleeftijd=60,
            max_wedstrijdleeftijd=0,
            volgens_wa=False),

        # >= 50
        leeftijdsklasse_klas(
            afkorting='MH', geslacht='M',
            klasse_kort='Master',
            beschrijving='Masters, mannen',
            volgorde=50,
            min_wedstrijdleeftijd=50,
            max_wedstrijdleeftijd=0,
            volgens_wa=True),
        leeftijdsklasse_klas(
            afkorting='MV', geslacht='V',
            klasse_kort='Master',
            beschrijving='Masters, vrouwen',
            volgorde=50,
            min_wedstrijdleeftijd=50,
            max_wedstrijdleeftijd=0,
            volgens_wa=True),

        # open klasse
        leeftijdsklasse_klas(
            afkorting='SH', geslacht='M',
            klasse_kort='Senior',
            beschrijving='Senioren, mannen',
            volgorde=40,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=0),
        leeftijdsklasse_klas(
            afkorting='SV', geslacht='V',
            klasse_kort='Senior',
            beschrijving='Senioren, vrouwen',
            volgorde=40,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=0),

        # <= 20
        leeftijdsklasse_klas(
            afkorting='JH', geslacht='M',
            klasse_kort='Junior',
            beschrijving='Junioren, mannen',
            volgorde=30,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20),
        leeftijdsklasse_klas(
            afkorting='JV', geslacht='V',
            klasse_kort='Junior',
            beschrijving='Junioren, vrouwen',
            volgorde=30,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=20),

        # <= 17
        leeftijdsklasse_klas(
            afkorting='CH', geslacht='M',
            klasse_kort='Cadet',
            beschrijving='Cadetten, jongens',
            volgorde=20,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=17),
        leeftijdsklasse_klas(
            afkorting='CV', geslacht='V',
            klasse_kort='Cadet',
            beschrijving='Cadetten, meisjes',
            volgorde=20,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=17),

        # <= 13
        leeftijdsklasse_klas(
            afkorting='AH2', geslacht='M',
            klasse_kort='Aspirant',
            beschrijving='Aspiranten 11-12, jongens',   # heet 11-12 ivm leeftijd in 1e jaar competitie..
            volgorde=15,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=13,
            volgens_wa=False),
        leeftijdsklasse_klas(
            afkorting='AV2', geslacht='V',
            klasse_kort='Aspirant',
            beschrijving='Aspiranten 11-12, meisjes',
            volgorde=15,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=13,
            volgens_wa=False),

        # <= 11
        leeftijdsklasse_klas(
            afkorting='AH1', geslacht='M',
            klasse_kort='Aspirant',
            beschrijving='Aspiranten <11, jongens',
            volgorde=10,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=11,
            volgens_wa=False),
        leeftijdsklasse_klas(
            afkorting='AV1', geslacht='V',
            klasse_kort='Aspirant',
            beschrijving='Aspiranten <11, meisjes',
            volgorde=10,
            min_wedstrijdleeftijd=0,
            max_wedstrijdleeftijd=11,
            volgens_wa=False),
    ]
    leeftijdsklasse_klas.objects.bulk_create(bulk)


def init_team_typen(apps, _):
    """ Maak de team typen aan """

    # team typen volgens spec v2.1, deel 3, tabel 3.3

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    boog_type_klas = apps.get_model('BasisTypen', 'BoogType')

    boog_r = boog_c = boog_bb = boog_ib = boog_lb = None
    for boog in boog_type_klas.objects.all():
        if boog.afkorting == 'R':
            boog_r = boog
        if boog.afkorting == 'C':
            boog_c = boog
        if boog.afkorting == 'BB':
            boog_bb = boog
        if boog.afkorting == 'IB':
            boog_ib = boog
        if boog.afkorting == 'LB':
            boog_lb = boog
    # for

    # maak de standaard team typen aan
    team_r = team_type_klas(afkorting='R',  volgorde='1', beschrijving='Recurve team')
    team_c = team_type_klas(afkorting='C',  volgorde='2', beschrijving='Compound team')
    team_bb = team_type_klas(afkorting='BB', volgorde='3', beschrijving='Barebow team')
    team_ib = team_type_klas(afkorting='IB', volgorde='4', beschrijving='Instinctive Bow team')
    team_lb = team_type_klas(afkorting='LB', volgorde='5', beschrijving='Longbow team')

    team_type_klas.objects.bulk_create([team_r, team_c, team_bb, team_ib, team_lb])

    team_r.boog_typen.add(boog_r, boog_bb, boog_ib, boog_lb)
    team_c.boog_typen.add(boog_c)
    team_bb.boog_typen.add(boog_bb, boog_ib, boog_lb)
    team_ib.boog_typen.add(boog_ib, boog_lb)
    team_lb.boog_typen.add(boog_lb)


def init_wedstrijdklassen_individueel(apps, _):
    """ Maak de wedstrijdklassen aan"""

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'IndivWedstrijdklasse')
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
    for tup in WKL_INDIV:
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
            if lkl.max_wedstrijdleeftijd <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT:
                wkl.is_aspirant_klasse = True

            lkl_lijst.append(lkl)
        # for

        bulk.append(wkl)
    # for

    indiv_wedstrijdklasse_klas.objects.bulk_create(bulk)

    # koppel nu de leeftijdsklassen aan elke wedstrijdklasse
    for wkl in indiv_wedstrijdklasse_klas.objects.all():
        lkl_lijst = volgorde2lkl[wkl.volgorde]
        wkl.leeftijdsklassen.set(lkl_lijst)
    # for


def init_wedstrijdklassen_team(apps, _):
    """ Maak de team wedstrijdklassen aan"""

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    team_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'TeamWedstrijdklasse')

    # maak een look-up table voor de team type afkortingen
    boog_afkorting2teamtype = dict()
    for team_type in team_type_klas.objects.all():
        boog_afkorting2teamtype[team_type.afkorting] = team_type
    # for

    bulk = list()
    for volgorde, beschrijving, teamtype_afkorting, blazoenen_18m, blazoenen_25m in WKL_TEAM:

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

        obj = team_wedstrijdklasse_klas(
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

    team_wedstrijdklasse_klas.objects.bulk_create(bulk)


def init_kalenderwedstrijdklassen(apps, _):
    """ Maak de kalender wedstrijdklassen aan """

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
    for volgorde, boog_afk, lkl_afk, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
        boog = afk2boog[boog_afk]
        lkl = afk2lkl[lkl_afk]
        obj = kalenderwedstrijdklasse_klas(
                        beschrijving=beschrijving,
                        boogtype=boog,
                        leeftijdsklasse=lkl,
                        volgorde=volgorde)
        bulk.append(obj)
    # for
    kalenderwedstrijdklasse_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('BasisTypen', 'm0022_squashed')]

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
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], max_length=1)),
                ('min_wedstrijdleeftijd', models.IntegerField()),
                ('max_wedstrijdleeftijd', models.IntegerField()),
                ('volgens_wa', models.BooleanField(default=True)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
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
                ('afkorting', models.CharField(max_length=2)),
                ('volgorde', models.CharField(default='?', max_length=1)),
                ('boog_typen', models.ManyToManyField(to='BasisTypen.BoogType')),
            ],
            options={
                'verbose_name': 'Team type',
                'verbose_name_plural': 'Team typen',
            },
        ),
        migrations.CreateModel(
            name='IndivWedstrijdklasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('niet_voor_rk_bk', models.BooleanField()),
                ('is_onbekend', models.BooleanField(default=False)),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.boogtype')),
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
                'verbose_name': 'Indiv Wedstrijdklasse',
                'verbose_name_plural': 'Indiv Wedstrijdklassen',
            },
        ),
        migrations.CreateModel(
            name='TeamWedstrijdklasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('team_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.teamtype')),
                ('blazoen1_25m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
                ('blazoen2_25m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
                ('blazoen1_18m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen2_18m_regio', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen1_18m_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen2_18m_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2)),
                ('blazoen_25m_rk_bk', models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2)),
            ],
            options={
                'verbose_name': 'Team Wedstrijdklasse',
                'verbose_name_plural': 'Team Wedstrijdklassen',
            },
        ),
        migrations.CreateModel(
            name='KalenderWedstrijdklasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('leeftijdsklasse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.leeftijdsklasse')),
            ],
            options={
                'verbose_name': 'KalenderWedstrijdklasse',
                'verbose_name_plural': 'KalenderWedstrijdklassen',
            },
        ),
        migrations.RunPython(init_boogtype),
        migrations.RunPython(init_leeftijdsklasse),
        migrations.RunPython(init_team_typen),
        migrations.RunPython(init_wedstrijdklassen_individueel),
        migrations.RunPython(init_wedstrijdklassen_team),
        migrations.RunPython(init_kalenderwedstrijdklassen),
    ]

# end of file
