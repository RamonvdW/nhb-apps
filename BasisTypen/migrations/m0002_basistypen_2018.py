# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def init_boogtype_2018(apps, schema_editor):
    """ Boog typen jaar 2018, volgens spec v1.2, tabel 2.2 """

    # haal de klassen op die van toepassing zijn vóór de migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # maak de standaard boogtypen aan
    boogtype_klas(afkorting='R',  beschrijving='Recurve').save()
    boogtype_klas(afkorting='C',  beschrijving='Compound').save()
    boogtype_klas(afkorting='BB', beschrijving='Barebow').save()
    boogtype_klas(afkorting='IB', beschrijving='Instinctive bow').save()
    boogtype_klas(afkorting='LB', beschrijving='Longbow').save()


def create_teamtype_boog(apps, beschrijving, boogtypen):
    """ Maak een teamtype record aan
        Koppel de gewenste boogtypen aan het teamtype door teamtypeboog records aan te maken

        inputs:
            apps:         not used
            beschrijving: beschrijving voor het nieuwe teamtype
            boogtypen:    lijst met boogtype.afkorting
    """

    # haal de klassen op die van toepassing zijn vóór de migratie
    teamtype_klas = apps.get_model('BasisTypen', 'TeamType')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')
    teamtypeboog_klas = apps.get_model('BasisTypen', 'TeamTypeBoog')

    # maak het nieuwe teamtype record aan met de gevraagde beschrijving
    teamtype = teamtype_klas(beschrijving=beschrijving)
    teamtype.save()

    # doorloop alle boogtypen en koppel deze aan het teamtype
    # door een teamtypeboog record aan te maken
    for rec in boogtype_klas.objects.all():
        if rec.afkorting in boogtypen:
            teamtypeboog_klas(boogtype=rec, teamtype=teamtype).save()
    # for


def init_teamtype_2018(apps, schema_editor):
    """ Maak de teamtype records aan """

    # team typen in jaar 2018, volgens spec v1.2, tabel 2.3
    TEAMTYPEN = (
        # beschrijving           boogtypen
        ('Recurve team',         ('R', 'BB', 'IB', 'LB')),
        ('Compound team',        ('C',)),
        ('Barebow team',         ('BB', 'IB', 'LB')),
        ('Instinctive Bow team', ('IB', 'LB')),
        ('Longbow team',         ('LB',))
    )

    for tup in TEAMTYPEN:
        create_teamtype_boog(apps, *tup)
    # for


def init_leeftijdsklasse_2018(apps, schema_editor):
    """ Maak de leeftijdsklassen aan """

    # leeftijdsklassen jaar 2018, volgens spec v1.2, tabel 2.1
    # note: wedstrijdleeftijd = leeftijd die je bereikt in een jaar
    #       competitieleeftijd = wedstrijdleeftijd + 1

    # haal de klassen op die van toepassing zijn vóór de migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    leeftijdsklasse_klas(
        afkorting='SH', geslacht='M',
        beschrijving='Senioren, mannen',
        max_wedstrijdleeftijd=150).save()
    leeftijdsklasse_klas(
        afkorting='SV', geslacht='V',
        beschrijving='Senioren, vrouwen',
        max_wedstrijdleeftijd=150).save()

    leeftijdsklasse_klas(
        afkorting='JH', geslacht='M',
        beschrijving='Junioren, mannen',
        max_wedstrijdleeftijd=20).save()
    leeftijdsklasse_klas(
        afkorting='JV', geslacht='V',
        beschrijving='Junioren, vrouwen',
        max_wedstrijdleeftijd=20).save()

    leeftijdsklasse_klas(
        afkorting='CH', geslacht='M',
        beschrijving='Cadetten, jongens',
        max_wedstrijdleeftijd=17).save()
    leeftijdsklasse_klas(
        afkorting='CV', geslacht='M',
        beschrijving='Cadetten, meisjes',
        max_wedstrijdleeftijd=17).save()

    leeftijdsklasse_klas(
        afkorting='AH2', geslacht='M',
        beschrijving='Aspiranten 11-12, jongens',
        max_wedstrijdleeftijd=12).save()
    leeftijdsklasse_klas(
        afkorting='AV2', geslacht='V',
        beschrijving='Aspiranten 11-12, meisjes',
        max_wedstrijdleeftijd=12).save()

    leeftijdsklasse_klas(
        afkorting='AH1', geslacht='M',
        beschrijving='Aspiranten <11, jongens',
        max_wedstrijdleeftijd=10).save()
    leeftijdsklasse_klas(
        afkorting='AV1', geslacht='V',
        beschrijving='Aspiranten <11, meisjes',
        max_wedstrijdleeftijd=10).save()


def create_wedstrijdklasse_individueel(apps, beschrijving, boogtypen, leeftijdsklassen, min_ag, niet_voor_rk_bk=False):
    """ Maak de wedstrijdklassen aan
        Koppel de gewenste boogtypen en leeftijdsklassen aan de wedstrijdklasse
    """

    # haal de klassen op die van toepassing zijn vóór de migratie
    wedstrijdklasse_klas = apps.get_model('BasisTypen', 'WedstrijdKlasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')
    wedstrijdklasseleeftijd_klas = apps.get_model('BasisTypen', 'WedstrijdKlasseLeeftijd')
    wedstrijdklasseboog_klas = apps.get_model('BasisTypen', 'WedstrijdKlasseBoog')

    wkl = wedstrijdklasse_klas(
            beschrijving=beschrijving,
            min_ag=min_ag,
            is_voor_teams=False,
            niet_voor_rk_bk=niet_voor_rk_bk)
    wkl.save()

    # doorloop alle boogtypen en koppel deze aan de wedstrijdklasse
    # door een wedstrijdklasseboog record aan te maken
    for rec in boogtype_klas.objects.all():
        if rec.afkorting in boogtypen:
            wedstrijdklasseboog_klas(boogtype=rec, wedstrijdklasse=wkl).save()
    # for

    # doorloop alle leeftijdsklassen en koppel deze aan de wedstrijdklasse
    # door een wedstrijdklasseleeftijd record aan te maken
    for rec in leeftijdsklasse_klas.objects.all():
        if rec.afkorting in leeftijdsklassen:
            wedstrijdklasseleeftijd_klas(leeftijdsklasse=rec, wedstrijdklasse=wkl).save()
    # for


def create_wedstrijdklasse_team(apps, beschrijving, boogtypen, min_ag):
    """ Maak de wedstrijdklassen aan voor teamwedstrijden
        Koppel de gewenste boogtypen aan de wedstrijdklasse
        (voor teams gelden geen leeftijdsklassen)
    """

    # haal de klassen op die van toepassing zijn vóór de migratie
    wedstrijdklasse_klas = apps.get_model('BasisTypen', 'WedstrijdKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')
    wedstrijdklasseboog_klas = apps.get_model('BasisTypen', 'WedstrijdKlasseBoog')

    wkl = wedstrijdklasse_klas(
            beschrijving=beschrijving,
            min_ag=min_ag,
            is_voor_teams=True,
            niet_voor_rk_bk=False)
    wkl.save()

    # doorloop alle boogtypen en koppel deze aan de wedstrijdklasse
    # door een wedstrijdklasseboog record aan te maken
    for rec in boogtype_klas.objects.all():
        if rec.afkorting in boogtypen:
            wedstrijdklasseboog_klas(boogtype=rec, wedstrijdklasse=wkl).save()
    # for


def init_wedstrijdklassen_2018(apps, schema_editor):
    # wedstrijdklassen jaar 2018 volgens spec v1.2, tabel 2.4 en 2.5

    # spec v1.2, tabel 2.4: wedstrijdklassen voor individuele competities
    WKL_INDIV = (
        ('Recurve klasse 1',               ('R', 'BB', 'IB', 'LB'), ('SH', 'SV'),         '9.000'),
        ('Recurve klasse 2',               ('R', 'BB', 'IB', 'LB'), ('SH', 'SV'),         '8.000'),
        ('Recurve klasse 3',               ('R', 'BB', 'IB', 'LB'), ('SH', 'SV'),         '7.000'),
        ('Recurve klasse 4',               ('R', 'BB', 'IB', 'LB'), ('SH', 'SV'),         '6.000'),
        ('Recurve klasse 5',               ('R', 'BB', 'IB', 'LB'), ('SH', 'SV'),         '5.000'),
        ('Recurve klasse 6',               ('R', 'BB', 'IB', 'LB'), ('SH', 'SV'),         '0.000'),
        ('Recurve Junioren klasse 1',      ('R', 'BB', 'IB', 'LB'), ('JH', 'JV'),         '8.000'),
        ('Recurve Junioren klasse 2',      ('R', 'BB', 'IB', 'LB'), ('JH', 'JV'),         '0.000'),
        ('Recurve Cadetten klasse 1',      ('R', 'BB', 'IB', 'LB'), ('CH', 'CV'),         '9.000'),
        ('Recurve Cadetten klasse 2',      ('R', 'BB', 'IB', 'LB'), ('CH', 'CV'),         '0.000'),
        ('Recurve Aspiranten < 11 jaar',   ('R', 'BB', 'IB', 'LB'), ('AH1', 'AV1'),       '0.000', True),
        ('Recurve Aspiranten 11-12 jaar',  ('R', 'BB', 'IB', 'LB'), ('AH2', 'AV2'),       '0.000', True),
        ('Compound klasse 1',              ('C',),  ('SH', 'SV'),                         '9.000'),
        ('Compound klasse 2',              ('C',),  ('SH', 'SV'),                         '0.000'),
        ('Compound Junioren klasse 1',     ('C',),  ('JH', 'JV'),                         '9.000'),
        ('Compound Junioren klasse 2',     ('C',),  ('JH', 'JV'),                         '0.000'),
        ('Compound Cadetten klasse 1',     ('C',),  ('CH', 'CV'),                         '9.000'),
        ('Compound Cadetten klasse 2',     ('C',),  ('CH', 'CV'),                         '0.000'),
        ('Compound Aspiranten < 11 jaar',  ('C',),  ('AH1', 'AV1'),                       '0.000', True),
        ('Compound Aspiranten 11-12 jaar', ('C',),  ('AH2', 'AV2'),                       '0.000', True),
        ('Barebow klasse 1',               ('BB',), ('SH', 'SV', 'JH', 'JV', 'CH', 'CV'), '5.000'),
        ('Barebow klasse 2',               ('BB',), ('SH', 'SV', 'JH', 'JV', 'CH', 'CV'), '0.000'),
        ('Instinctive Bow klasse 1',       ('IB',), ('SH', 'SV', 'JH', 'JV', 'CH', 'CV'), '5.000'),
        ('Instinctive Bow klasse 2',       ('IB',), ('SH', 'SV', 'JH', 'JV', 'CH', 'CV'), '0.000'),
        ('Longbow klasse 1',               ('LB',), ('SH', 'SV', 'JH', 'JV', 'CH', 'CV'), '5.000'),
        ('Longbow klasse 2',               ('LB',), ('SH', 'SV', 'JH', 'JV', 'CH', 'CV'), '0.000'),
    )

    for tup in WKL_INDIV:
        create_wedstrijdklasse_individueel(apps, *tup)
    # for

    WKL_TEAM = (
        ('Recurve klasse ERE',         ('R', 'BB', 'IB', 'LB'), '9.000'),
        ('Recurve klasse A',           ('R', 'BB', 'IB', 'LB'), '8.000'),
        ('Recurve klasse B',           ('R', 'BB', 'IB', 'LB'), '7.000'),
        ('Recurve klasse C',           ('R', 'BB', 'IB', 'LB'), '6.000'),
        ('Recurve klasse D',           ('R', 'BB', 'IB', 'LB'), '0.000'),
        ('Compound klasse ERE',        ('C',),                  '9.000'),
        ('Compound klasse A',          ('C',),                  '0.000'),
        ('Barebow klasse ERE',         ('BB', 'IB', 'LB'),      '0.000'),
        ('Instinctive Bow klasse ERE', ('IB', 'LB'),            '0.000'),
        ('Longbow klasse ERE',         ('LB',),                 '0.000'),
    )

    for tup in WKL_TEAM:
        create_wedstrijdklasse_team(apps, *tup)
    # for


class Migration(migrations.Migration):
    """ Migratie classs voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(init_boogtype_2018),
        migrations.RunPython(init_teamtype_2018),
        migrations.RunPython(init_leeftijdsklasse_2018),
        migrations.RunPython(init_wedstrijdklassen_2018),
    ]

# end of file

