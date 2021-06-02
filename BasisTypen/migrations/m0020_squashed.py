# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def init_boogtype(apps, _):
    """ Maak de boog typen aan """

    # boog typen volgens spec v2.1, tabel 3.2

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # maak de standaard boogtypen aan
    boogtype_klas(afkorting='R',  volgorde='A', beschrijving='Recurve').save()
    boogtype_klas(afkorting='C',  volgorde='D', beschrijving='Compound').save()
    boogtype_klas(afkorting='BB', volgorde='I', beschrijving='Barebow').save()
    boogtype_klas(afkorting='IB', volgorde='M', beschrijving='Instinctive bow').save()
    boogtype_klas(afkorting='LB', volgorde='S', beschrijving='Longbow').save()


def init_leeftijdsklasse(apps, _):
    """ Maak de leeftijdsklassen aan """

    # leeftijdsklassen volgens spec v2.1, deel 3, tabel 3.1

    # note: wedstrijdleeftijd = leeftijd die je bereikt in een jaar
    #       competitieleeftijd = wedstrijdleeftijd + 1

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    # 60+
    leeftijdsklasse_klas(
        afkorting='VH', geslacht='M',
        klasse_kort='Veteraan',
        beschrijving='Veteranen, mannen',
        volgorde=60,
        min_wedstrijdleeftijd=60,
        max_wedstrijdleeftijd=0,
        volgens_wa=False).save()
    leeftijdsklasse_klas(
        afkorting='VV', geslacht='V',
        klasse_kort='Veteraan',
        beschrijving='Veteranen, vrouwen',
        volgorde=60,
        min_wedstrijdleeftijd=60,
        max_wedstrijdleeftijd=0,
        volgens_wa=False).save()

    # 50..59
    leeftijdsklasse_klas(
        afkorting='MH', geslacht='M',
        klasse_kort='Master',
        beschrijving='Masters, mannen',
        volgorde=50,
        min_wedstrijdleeftijd=50,
        max_wedstrijdleeftijd=0,
        volgens_wa=True).save()
    leeftijdsklasse_klas(
        afkorting='MV', geslacht='V',
        klasse_kort='Master',
        beschrijving='Masters, vrouwen',
        volgorde=50,
        min_wedstrijdleeftijd=50,
        max_wedstrijdleeftijd=0,
        volgens_wa=True).save()

    # 21..49
    leeftijdsklasse_klas(
        afkorting='SH', geslacht='M',
        klasse_kort='Senior',
        beschrijving='Senioren, mannen',
        volgorde=40,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=49).save()
    leeftijdsklasse_klas(
        afkorting='SV', geslacht='V',
        klasse_kort='Senior',
        beschrijving='Senioren, vrouwen',
        volgorde=40,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=49).save()

    # 18, 19, 20
    leeftijdsklasse_klas(
        afkorting='JH', geslacht='M',
        klasse_kort='Junior',
        beschrijving='Junioren, mannen',
        volgorde=30,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=20).save()
    leeftijdsklasse_klas(
        afkorting='JV', geslacht='V',
        klasse_kort='Junior',
        beschrijving='Junioren, vrouwen',
        volgorde=30,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=20).save()

    # 14, 15, 16, 17
    leeftijdsklasse_klas(
        afkorting='CH', geslacht='M',
        klasse_kort='Cadet',
        beschrijving='Cadetten, jongens',
        volgorde=20,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=17).save()
    leeftijdsklasse_klas(
        afkorting='CV', geslacht='V',
        klasse_kort='Cadet',
        beschrijving='Cadetten, meisjes',
        volgorde=20,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=17).save()

    # 12 + 13
    leeftijdsklasse_klas(
        afkorting='AH2', geslacht='M',
        klasse_kort='Aspirant',
        beschrijving='Aspiranten 11-12, jongens',   # heet 11-12 ivm leeftijd in 1e jaar competitie..
        volgorde=15,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=13,
        volgens_wa=False).save()
    leeftijdsklasse_klas(
        afkorting='AV2', geslacht='V',
        klasse_kort='Aspirant',
        beschrijving='Aspiranten 11-12, meisjes',
        volgorde=15,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=13,
        volgens_wa=False).save()

    # 10 + 11
    leeftijdsklasse_klas(
        afkorting='AH1', geslacht='M',
        klasse_kort='Aspirant',
        beschrijving='Aspiranten <11, jongens',
        volgorde=10,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=11,
        volgens_wa=False).save()
    leeftijdsklasse_klas(
        afkorting='AV1', geslacht='V',
        klasse_kort='Aspirant',
        beschrijving='Aspiranten <11, meisjes',
        volgorde=10,
        min_wedstrijdleeftijd=0,
        max_wedstrijdleeftijd=11,
        volgens_wa=False).save()


def init_team_typen(apps, _):
    """ Maak de team typen aan """

    # team typen volgens spec v2.1, deel 3, tabel 3.3

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    boog_type_klas = apps.get_model('BasisTypen', 'BoogType')

    boog_r = boog_type_klas.objects.get(afkorting='R')
    boog_c = boog_type_klas.objects.get(afkorting='C')
    boog_bb = boog_type_klas.objects.get(afkorting='BB')
    boog_ib = boog_type_klas.objects.get(afkorting='IB')
    boog_lb = boog_type_klas.objects.get(afkorting='LB')

    # maak de standaard team typen aan
    team = team_type_klas(afkorting='R',  volgorde='1', beschrijving='Recurve team')
    team.save()
    team.boog_typen.add(boog_r, boog_bb, boog_ib, boog_lb)

    team = team_type_klas(afkorting='C',  volgorde='2', beschrijving='Compound team')
    team.save()
    team.boog_typen.add(boog_c)

    team = team_type_klas(afkorting='BB', volgorde='3', beschrijving='Barebow team')
    team.save()
    team.boog_typen.add(boog_bb, boog_ib, boog_lb)

    team = team_type_klas(afkorting='IB', volgorde='4', beschrijving='Instinctive Bow team')
    team.save()
    team.boog_typen.add(boog_ib, boog_lb)

    team = team_type_klas(afkorting='LB', volgorde='5', beschrijving='Longbow team')
    team.save()
    team.boog_typen.add(boog_lb)


# individuele wedstrijdklassen volgens spec v2.1, deel 3, tabel 3.4
WKL_INDIV = (
    (100, 'Recurve klasse 1',                      'R',  ('SH', 'SV')),
    (101, 'Recurve klasse 2',                      'R',  ('SH', 'SV')),
    (102, 'Recurve klasse 3',                      'R',  ('SH', 'SV')),
    (103, 'Recurve klasse 4',                      'R',  ('SH', 'SV')),
    (104, 'Recurve klasse 5',                      'R',  ('SH', 'SV')),
    (105, 'Recurve klasse 6',                      'R',  ('SH', 'SV')),
    (109, 'Recurve klasse onbekend',               'R',  ('SH', 'SV')),

    (110, 'Recurve Junioren klasse 1',             'R',  ('JH', 'JV')),
    (111, 'Recurve Junioren klasse 2',             'R',  ('JH', 'JV')),
    (119, 'Recurve Junioren klasse onbekend',      'R',  ('JH', 'JV')),

    (120, 'Recurve Cadetten klasse 1',             'R',  ('CH', 'CV')),
    (121, 'Recurve Cadetten klasse 2',             'R',  ('CH', 'CV')),
    (129, 'Recurve Cadetten klasse onbekend',      'R',  ('CH', 'CV')),

    (150, 'Recurve Aspiranten 11-12 jaar',         'R',  ('AH2', 'AV2'), True),
    (155, 'Recurve Aspiranten < 11 jaar',          'R',  ('AH1', 'AV1'), True),


    (200, 'Compound klasse 1',                     'C',  ('SH', 'SV')),
    (201, 'Compound klasse 2',                     'C',  ('SH', 'SV')),
    (209, 'Compound klasse onbekend',              'C',  ('SH', 'SV')),

    (210, 'Compound Junioren klasse 1',            'C',  ('JH', 'JV')),
    (211, 'Compound Junioren klasse 2',            'C',  ('JH', 'JV')),
    (219, 'Compound Junioren klasse onbekend',     'C',  ('JH', 'JV')),

    (220, 'Compound Cadetten klasse 1',            'C',  ('CH', 'CV')),
    (221, 'Compound Cadetten klasse 2',            'C',  ('CH', 'CV')),
    (229, 'Compound Cadetten klasse onbekend',     'C',  ('CH', 'CV')),

    (250, 'Compound Aspiranten 11-12 jaar',        'C',  ('AH2', 'AV2'), True),
    (255, 'Compound Aspiranten < 11 jaar',         'C',  ('AH1', 'AV1'), True),


    (300, 'Barebow klasse 1',                      'BB', ('SH', 'SV')),
    (301, 'Barebow klasse 2',                      'BB', ('SH', 'SV')),
    (309, 'Barebow klasse onbekend',               'BB', ('SH', 'SV')),

    (310, 'Barebow Jeugd klasse 1',                'BB', ('JH', 'JV', 'CH', 'CV')),

    (350, 'Barebow Aspiranten 11-12 jaar',         'BB', ('AH2', 'AV2'), True),
    (355, 'Barebow Aspiranten < 11 jaar',          'BB', ('AH1', 'AV1'), True),


    (400, 'Instinctive Bow klasse 1',              'IB', ('SH', 'SV')),
    (401, 'Instinctive Bow klasse 2',              'IB', ('SH', 'SV')),
    (409, 'Instinctive Bow klasse onbekend',       'IB', ('SH', 'SV')),

    (410, 'Instinctive Bow Jeugd klasse 1',        'IB', ('JH', 'JV', 'CH', 'CV')),

    (450, 'Instinctive Bow Aspiranten 11-12 jaar', 'IB', ('AH2', 'AV2'), True),
    (455, 'Instinctive Bow Aspiranten < 11 jaar',  'IB', ('AH1', 'AV1'), True),


    (500, 'Longbow klasse 1',                      'LB', ('SH', 'SV')),
    (501, 'Longbow klasse 2',                      'LB', ('SH', 'SV')),
    (509, 'Longbow klasse onbekend',               'LB', ('SH', 'SV')),

    (510, 'Longbow Jeugd klasse 1',                'LB', ('JH', 'JV', 'CH', 'CV')),

    (550, 'Longbow Aspiranten 11-12 jaar',         'LB', ('AH2', 'AV2'), True),
    (555, 'Longbow Aspiranten < 11 jaar',          'LB', ('AH1', 'AV1'), True),
)


def init_wedstrijdklassen_individueel(apps, _):
    """ Maak de wedstrijdklassen aan"""

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'IndivWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # maak een look-up table voor de boog afkortingen
    afkorting2boogtype = dict()
    for obj in boogtype_klas.objects.all():
        afkorting2boogtype[obj.afkorting] = obj
    # for

    for tup in WKL_INDIV:
        if len(tup) == 4:
            volgorde, beschrijving, boog_afkorting, leeftijdsklassen = tup
            niet_voor_rk_bk = False
        else:
            volgorde, beschrijving, boog_afkorting, leeftijdsklassen, niet_voor_rk_bk = tup

        boogtype_obj = afkorting2boogtype[boog_afkorting]
        is_onbekend = 'onbekend' in beschrijving
        if is_onbekend:
            niet_voor_rk_bk = True

        wkl = indiv_wedstrijdklasse_klas(
                    beschrijving=beschrijving,
                    volgorde=volgorde,
                    boogtype=boogtype_obj,
                    niet_voor_rk_bk=niet_voor_rk_bk,
                    is_onbekend=is_onbekend)
        wkl.save()

        # koppel de gewenste leeftijdsklassen aan de wedstrijdklasse
        lkl = list()
        for obj in leeftijdsklasse_klas.objects.all():
            if obj.afkorting in leeftijdsklassen:
                lkl.append(obj)
        # for
        wkl.leeftijdsklassen.set(lkl)
    # for


# team wedstrijdklassen volgens spec v2.1, deel 3, tabel 3.5
WKL_TEAM = (
    (10, 'Recurve klasse ERE',         'R'),        # R = team type
    (11, 'Recurve klasse A',           'R'),
    (12, 'Recurve klasse B',           'R'),
    (13, 'Recurve klasse C',           'R'),
    (14, 'Recurve klasse D',           'R'),

    (20, 'Compound klasse ERE',        'C'),
    (21, 'Compound klasse A',          'C'),

    (30, 'Barebow klasse ERE',         'BB'),

    (40, 'Instinctive Bow klasse ERE', 'IB'),

    (50, 'Longbow klasse ERE',         'LB'),
)


def init_wedstrijdklassen_team(apps, _):
    """ Maak de team wedstrijdklassen aan"""

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_type_klas = apps.get_model('BasisTypen', 'TeamType')
    team_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'TeamWedstrijdklasse')

    # maak een look-up table voor de team type afkortingen
    afkorting2teamtype = dict()
    for team_type in team_type_klas.objects.all():
        afkorting2teamtype[team_type.afkorting] = team_type
    # for

    bulk = list()
    for volgorde, beschrijving, teamtype_afkorting in WKL_TEAM:
        teamtype = afkorting2teamtype[teamtype_afkorting]
        obj = team_wedstrijdklasse_klas(
                    beschrijving=beschrijving,
                    volgorde=volgorde,
                    team_type=teamtype)
        bulk.append(obj)
    # for

    team_wedstrijdklasse_klas.objects.bulk_create(bulk)


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
