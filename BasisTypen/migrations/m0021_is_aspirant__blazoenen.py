# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.models import (MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT,
                               BLAZOEN_40CM, BLAZOEN_DT,
                               BLAZOEN_60CM, BLAZOEN_60CM_4SPOT)


# team wedstrijdklassen volgens spec v2.1, deel 3, tabel 3.5
WKL_TEAM = (                                 # 18m                          # 25m
                                             # regio1/2 == rk-bk1/2         # regio1, regio2, rk/bk
    (10, 'Recurve klasse ERE',         'R',  (BLAZOEN_40CM, BLAZOEN_DT),    (BLAZOEN_60CM,)),        # R = team type
    (11, 'Recurve klasse A',           'R',  (BLAZOEN_40CM,),               (BLAZOEN_60CM,)),
    (12, 'Recurve klasse B',           'R',  (BLAZOEN_40CM,),               (BLAZOEN_60CM,)),
    (13, 'Recurve klasse C',           'R',  (BLAZOEN_40CM,),               (BLAZOEN_60CM,)),
    (14, 'Recurve klasse D',           'R',  (BLAZOEN_40CM,),               (BLAZOEN_60CM,)),

    (20, 'Compound klasse ERE',        'C',  (BLAZOEN_DT,),                 (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),
    (21, 'Compound klasse A',          'C',  (BLAZOEN_DT,),                 (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT, BLAZOEN_60CM_4SPOT)),

    (30, 'Barebow klasse ERE',         'BB', (BLAZOEN_40CM,),               (BLAZOEN_60CM,)),

    (40, 'Instinctive Bow klasse ERE', 'IB', (BLAZOEN_40CM,),               (BLAZOEN_60CM,)),

    (50, 'Longbow klasse ERE',         'LB', (BLAZOEN_40CM,),               (BLAZOEN_60CM,)),
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


# for some reason the LeeftijdsKlasse class available in this context does not have the method found on the model
# work-around: copy of the function
def is_aspirant_klasse(lkl):
    # <senior  heeft min = 0 en max <21
    # senior   heeft min = 0 en max = 0
    # >senior  heeft min >49 en max = 0     (komt niet voor in de competitie)
    return 0 < lkl.max_wedstrijdleeftijd <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT


def zet_asp_en_blazoen_individueel(apps, _):
    """ Zet de nieuwe is_aspirant_klasse ahv de leeftijdsklassen
        Zet de blazoenen voor de individuele bondscompetitie klassen
    """
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_klas = apps.get_model('BasisTypen', 'IndivWedstrijdklasse')

    volgorde2indiv = dict()       # [volgorde] = IndivWedstrijdklasse
    for klasse in (indiv_klas.objects.all()):           # pragma: no cover
        volgorde2indiv[klasse.volgorde] = klasse

        # bepaal of deze klasse voor aspiranten is
        for lkl in klasse.leeftijdsklassen.all():
            if is_aspirant_klasse(lkl):
                klasse.is_aspirant_klasse = True
                break  # from the for
        # for
    # for

    # zet de blazoenen voor de individuele klassen
    for tup in WKL_INDIV:
        if len(tup) == 6:
            volgorde, beschrijving, boog_afkorting, leeftijdsklassen, blazoenen_18m, blazoenen_25m = tup
            niet_voor_rk_bk = False
        else:
            volgorde, beschrijving, boog_afkorting, leeftijdsklassen, blazoenen_18m, blazoenen_25m, niet_voor_rk_bk = tup

        is_onbekend = 'onbekend' in beschrijving
        if is_onbekend:
            niet_voor_rk_bk = True

        wkl = volgorde2indiv[volgorde]

        # blazoen is 1 of 3 lang
        blazoenen_18m = list(blazoenen_18m)
        while len(blazoenen_18m) < 3:
            blazoenen_18m.append(blazoenen_18m[0])
        # while

        blazoenen_25m = list(blazoenen_25m)
        while len(blazoenen_25m) < 3:
            blazoenen_25m.append(blazoenen_25m[0])
        # while

        wkl.blazoen1_18m_regio, wkl.blazoen2_18m_regio, wkl.blazoen_18m_rk_bk = blazoenen_18m
        wkl.blazoen1_25m_regio, wkl.blazoen2_25m_regio, wkl.blazoen_25m_rk_bk = blazoenen_25m
    # for

    # save alle individuele klassen
    for klasse in volgorde2indiv.values():
        klasse.save(update_fields=['is_aspirant_klasse',
                                   'blazoen1_18m_regio', 'blazoen2_18m_regio', 'blazoen_18m_rk_bk',
                                   'blazoen1_25m_regio', 'blazoen2_25m_regio', 'blazoen_25m_rk_bk'])
    # for


def zet_blazoen_team(apps, _):
    """ Zet de nieuwe is_aspirant_klasse ahv de leeftijdsklassen
        Zet de blazoenen voor de individuele bondscompetitie klassen
    """
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_klas = apps.get_model('BasisTypen', 'TeamWedstrijdklasse')

    volgorde2team = dict()       # [volgorde] = IndivWedstrijdklasse
    for klasse in (team_klas.objects.all()):           # pragma: no cover
        volgorde2team[klasse.volgorde] = klasse
    # for

    # zet de blazoenen voor de individuele klassen
    for volgorde, beschrijving, teamtype_afkorting, blazoenen_18m, blazoenen_25m in WKL_TEAM:

        klasse = volgorde2team[volgorde]

        # blazoenen_18m is 1 of 2 lang; dezelfde toepassing voor regio en RK/BK
        blazoenen_18m = list(blazoenen_18m)
        if len(blazoenen_18m) < 2:
            blazoenen_18m.append(blazoenen_18m[0])
        klasse.blazoen1_18m_regio = klasse.blazoen1_18m_rk_bk = blazoenen_18m[0]
        klasse.blazoen2_18m_regio = klasse.blazoen2_18m_rk_bk = blazoenen_18m[1]

        # blazoenen_25m is 1 of 3 lang (1 = repeated up to 3), daarna: 1+2 voor regio en 3 voor rk/bk
        blazoenen_25m = list(blazoenen_25m)
        while len(blazoenen_25m) < 3:
            blazoenen_25m.append(blazoenen_25m[0])
        # while
        klasse.blazoen1_25m_regio, klasse.blazoen2_25m_regio, klasse.blazoen_25m_rk_bk = blazoenen_25m

        klasse.save(update_fields=['blazoen1_18m_regio', 'blazoen2_18m_regio', 'blazoen1_18m_rk_bk', 'blazoen2_18m_rk_bk',
                                   'blazoen1_25m_regio', 'blazoen2_25m_regio', 'blazoen_25m_rk_bk'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0020_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='indivwedstrijdklasse',
            name='blazoen1_18m_regio',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2),
        ),
        migrations.AddField(
            model_name='indivwedstrijdklasse',
            name='blazoen1_25m_regio',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2),
        ),
        migrations.AddField(
            model_name='indivwedstrijdklasse',
            name='blazoen2_18m_regio',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2),
        ),
        migrations.AddField(
            model_name='indivwedstrijdklasse',
            name='blazoen2_25m_regio',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2),
        ),
        migrations.AddField(
            model_name='indivwedstrijdklasse',
            name='blazoen_18m_rk_bk',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2),
        ),
        migrations.AddField(
            model_name='indivwedstrijdklasse',
            name='blazoen_25m_rk_bk',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2),
        ),
        migrations.AddField(
            model_name='indivwedstrijdklasse',
            name='is_aspirant_klasse',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(zet_asp_en_blazoen_individueel),

        migrations.AddField(
            model_name='teamwedstrijdklasse',
            name='blazoen1_25m_regio',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2),
        ),
        migrations.AddField(
            model_name='teamwedstrijdklasse',
            name='blazoen2_25m_regio',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2),
        ),
        migrations.AddField(
            model_name='teamwedstrijdklasse',
            name='blazoen1_18m_regio',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2),
        ),
        migrations.AddField(
            model_name='teamwedstrijdklasse',
            name='blazoen2_18m_regio',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2),
        ),
        migrations.AddField(
            model_name='teamwedstrijdklasse',
            name='blazoen1_18m_rk_bk',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2),
        ),
        migrations.AddField(
            model_name='teamwedstrijdklasse',
            name='blazoen2_18m_rk_bk',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='40', max_length=2),
        ),
        migrations.AddField(
            model_name='teamwedstrijdklasse',
            name='blazoen_25m_rk_bk',
            field=models.CharField(choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')], default='60', max_length=2),
        ),
        migrations.RunPython(zet_blazoen_team),
    ]

# end of file
