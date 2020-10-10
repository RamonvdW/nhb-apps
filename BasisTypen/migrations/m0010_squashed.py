# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def init_boogtype_2018(apps, _):
    """ Boog typen jaar 2018, volgens spec v1.2, tabel 2.2 """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # maak de standaard boogtypen aan
    boogtype_klas(afkorting='R',  volgorde='A', beschrijving='Recurve').save()
    boogtype_klas(afkorting='C',  volgorde='D', beschrijving='Compound').save()
    boogtype_klas(afkorting='BB', volgorde='I', beschrijving='Barebow').save()
    boogtype_klas(afkorting='IB', volgorde='M', beschrijving='Instinctive bow').save()
    boogtype_klas(afkorting='LB', volgorde='S', beschrijving='Longbow').save()


def init_leeftijdsklasse_2018(apps, _):
    """ Maak de leeftijdsklassen aan """

    # leeftijdsklassen jaar 2018, volgens spec v1.2, tabel 2.1
    # note: wedstrijdleeftijd = leeftijd die je bereikt in een jaar
    #       competitieleeftijd = wedstrijdleeftijd + 1

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    leeftijdsklasse_klas(
        afkorting='SH', geslacht='M',
        klasse_kort='Senior',
        beschrijving='Senioren, mannen',
        min_wedstrijdleeftijd=21,
        max_wedstrijdleeftijd=150).save()
    leeftijdsklasse_klas(
        afkorting='SV', geslacht='V',
        klasse_kort='Senior',
        beschrijving='Senioren, vrouwen',
        min_wedstrijdleeftijd=21,
        max_wedstrijdleeftijd=150).save()

    # 18, 19, 20
    leeftijdsklasse_klas(
        afkorting='JH', geslacht='M',
        klasse_kort='Junior',
        beschrijving='Junioren, mannen',
        min_wedstrijdleeftijd=18,
        max_wedstrijdleeftijd=20).save()
    leeftijdsklasse_klas(
        afkorting='JV', geslacht='V',
        klasse_kort='Junior',
        beschrijving='Junioren, vrouwen',
        min_wedstrijdleeftijd=18,
        max_wedstrijdleeftijd=20).save()

    # 14, 15, 16, 17
    leeftijdsklasse_klas(
        afkorting='CH', geslacht='M',
        klasse_kort='Cadet',
        beschrijving='Cadetten, jongens',
        min_wedstrijdleeftijd=14,
        max_wedstrijdleeftijd=17).save()
    leeftijdsklasse_klas(
        afkorting='CV', geslacht='V',
        klasse_kort='Cadet',
        beschrijving='Cadetten, meisjes',
        min_wedstrijdleeftijd=14,
        max_wedstrijdleeftijd=17).save()

    # 12 + 13
    leeftijdsklasse_klas(
        afkorting='AH2', geslacht='M',
        klasse_kort='Aspirant',
        beschrijving='Aspiranten 11-12, jongens',   # heet 11-12 ivm leeftijd in 1e jaar competitie..
        min_wedstrijdleeftijd=12,
        max_wedstrijdleeftijd=13).save()
    leeftijdsklasse_klas(
        afkorting='AV2', geslacht='V',
        klasse_kort='Aspirant',
        beschrijving='Aspiranten 11-12, meisjes',
        min_wedstrijdleeftijd=12,
        max_wedstrijdleeftijd=13).save()

    # 10 + 11
    leeftijdsklasse_klas(
        afkorting='AH1', geslacht='M',
        klasse_kort='Aspirant',
        beschrijving='Aspiranten <11, jongens',
        min_wedstrijdleeftijd=1,
        max_wedstrijdleeftijd=11).save()
    leeftijdsklasse_klas(
        afkorting='AV1', geslacht='V',
        klasse_kort='Aspirant',
        beschrijving='Aspiranten <11, meisjes',
        min_wedstrijdleeftijd=1,
        max_wedstrijdleeftijd=11).save()


# individuele wedstrijdklassen jaar 2020 volgens spec v1.3, tabel 2.4
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


# individuele wedstrijdklassen jaar 2020 volgens spec v1.3, tabel 2.4
WKL_TEAM = (
    (10, 'Recurve klasse ERE',         ('R', 'BB', 'IB', 'LB')),
    (11, 'Recurve klasse A',           ('R', 'BB', 'IB', 'LB')),
    (12, 'Recurve klasse B',           ('R', 'BB', 'IB', 'LB')),
    (13, 'Recurve klasse C',           ('R', 'BB', 'IB', 'LB')),
    (14, 'Recurve klasse D',           ('R', 'BB', 'IB', 'LB')),

    (20, 'Compound klasse ERE',        ('C',)),
    (21, 'Compound klasse A',          ('C',)),

    (30, 'Barebow klasse ERE',         ('BB', 'IB', 'LB')),

    (40, 'Instinctive Bow klasse ERE', ('IB', 'LB')),

    (50, 'Longbow klasse ERE',         ('LB',)),
)


def create_wedstrijdklasse_individueel(apps, volgorde, beschrijving, boogtype_afkorting, leeftijdsklassen, niet_voor_rk_bk=False):
    """ Maak de wedstrijdklassen aan
        Koppel de gewenste leeftijdsklassen aan de wedstrijdklasse
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'IndivWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    boogtype_obj = boogtype_klas.objects.get(afkorting=boogtype_afkorting)
    is_onbekend = 'onbekend' in beschrijving

    wkl = indiv_wedstrijdklasse_klas(
            beschrijving=beschrijving,
            volgorde=volgorde,
            boogtype=boogtype_obj,
            niet_voor_rk_bk=niet_voor_rk_bk,
            is_onbekend=is_onbekend)
    wkl.save()

    # doorloop alle leeftijdsklassen en koppel deze aan de wedstrijdklasse
    # door een wedstrijdklasseleeftijd record aan te maken
    for rec in leeftijdsklasse_klas.objects.all():
        if rec.afkorting in leeftijdsklassen:
            wkl.leeftijdsklassen.add(rec)
    # for


def create_wedstrijdklasse_team(apps, volgorde, beschrijving, boogtypen):
    """ Maak de wedstrijdklassen aan voor teamwedstrijden
        Koppel de gewenste boogtypen aan de wedstrijdklasse
        (voor teams gelden geen leeftijdsklassen)
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'TeamWedstrijdklasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    wkl = team_wedstrijdklasse_klas(
            beschrijving=beschrijving,
            volgorde=volgorde)
    wkl.save()

    # doorloop alle boogtypen en koppel deze aan de wedstrijdklasse
    # door een wedstrijdklasseboog record aan te maken
    for rec in boogtype_klas.objects.all():
        if rec.afkorting in boogtypen:
            wkl.boogtypen.add(rec)
    # for


def init_wedstrijdklassen_2020(apps, _):
    """ Maak de wedstrijdklassen aan"""

    for tup in WKL_INDIV:
        create_wedstrijdklasse_individueel(apps, *tup)
    # for

    for tup in WKL_TEAM:
        create_wedstrijdklasse_team(apps, *tup)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
    ]

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
            ],
            options={
                'verbose_name': 'Leeftijdsklasse',
                'verbose_name_plural': 'Leeftijdsklassen',
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
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.BoogType')),
                ('leeftijdsklassen', models.ManyToManyField(to='BasisTypen.LeeftijdsKlasse')),
            ],
            options={
                'verbose_name': 'Wedstrijdklasse',
                'verbose_name_plural': 'Wedstrijdklassen',
            },
        ),
        migrations.CreateModel(
            name='TeamWedstrijdklasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('boogtypen', models.ManyToManyField(to='BasisTypen.BoogType')),
            ],
            options={
                'verbose_name': 'Team Wedstrijdklasse',
                'verbose_name_plural': 'Team Wedstrijdklassen',
            },
        ),
        migrations.RunPython(init_boogtype_2018),
        migrations.RunPython(init_leeftijdsklasse_2018),
        migrations.RunPython(init_wedstrijdklassen_2020),
    ]

# end of file
